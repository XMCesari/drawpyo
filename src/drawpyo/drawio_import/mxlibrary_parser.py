import base64
import html
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


def _decode_library_xml(xml_encoded: str) -> str:
    """Decode the XML payload stored in a draw.io mxlibrary item."""
    xml_str = html.unescape(xml_encoded)
    stripped = xml_str.lstrip()

    if stripped.startswith("<"):
        return xml_str

    if stripped.lower().startswith("%3c"):
        return urllib.parse.unquote(xml_str)

    try:
        compressed = base64.b64decode(xml_str.strip(), validate=True)
    except Exception:
        return urllib.parse.unquote(xml_str)

    for window_bits in (-15, zlib.MAX_WBITS):
        try:
            decoded = zlib.decompress(compressed, window_bits).decode("utf-8")
            return urllib.parse.unquote(decoded)
        except Exception:
            continue

    return xml_str


def _is_structural_cell(cell: ET.Element) -> bool:
    """Return True for draw.io boilerplate root/layer cells (id='0' or empty id='1')."""
    cell_id = cell.get("id")
    if cell_id == "0":
        return True
    if (
        cell_id == "1"
        and cell.get("parent") == "0"
        and not cell.get("vertex")
        and not cell.get("edge")
        and not cell.get("style")
        and not cell.get("value")
        and cell.find("mxGeometry") is None
    ):
        return True
    return False


def _parse_number(raw: Optional[str]) -> Optional[Union[int, float]]:
    """Parse a numeric XML attribute into int or float when present."""
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return int(value) if value.is_integer() else value


def _extract_cell_definition(cell: ET.Element, fallback_idx: int) -> Dict[str, Any]:
    """Extract style, hierarchy, and geometry attributes from an mxCell element."""
    geom = cell.find("mxGeometry")
    return {
        "id": cell.get("id") or f"cell_{fallback_idx}",
        "parent": cell.get("parent") or "1",
        "style": cell.get("style", ""),
        "value": cell.get("value", ""),
        "vertex": cell.get("vertex"),
        "edge": cell.get("edge"),
        "connectable": cell.get("connectable"),
        "source": cell.get("source"),
        "target": cell.get("target"),
        "geometry": {
            "x": _parse_number(geom.get("x")) if geom is not None else None,
            "y": _parse_number(geom.get("y")) if geom is not None else None,
            "width": _parse_number(geom.get("width")) if geom is not None else None,
            "height": _parse_number(geom.get("height")) if geom is not None else None,
            "relative": geom.get("relative") == "1" if geom is not None else False,
        },
    }


def _select_primary_style(cell_defs: List[Dict[str, Any]]) -> str:
    """Select a representative baseStyle for compound multi-cell icons."""
    for cell_def in cell_defs:
        style = cell_def.get("style", "")
        if "shape=stencil(" in style:
            return style
    for cell_def in cell_defs:
        if cell_def.get("vertex") == "1" and cell_def.get("style"):
            return cell_def["style"]
    for cell_def in cell_defs:
        if cell_def.get("style"):
            return cell_def["style"]
    return ""


def parse_mxlibrary(content: str) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """
    Parses an mxlibrary file content and extracts shape definitions.

    Args:
        content: The string content of the mxlibrary file.

    Returns:
        A tuple of (shapes_dict, errors_list) where:
        - shapes_dict: Dictionary with keys as titles and values as dicts containing
          properties like baseStyle, width, height, xml_class, and optional cells
          for compound multi-cell icons.
        - errors_list: List of error messages for shapes that couldn't be parsed.
    """
    errors: List[str] = []
    clean_content = (
        content.replace("<mxlibrary>", "").replace("</mxlibrary>", "").strip()
    )

    try:
        data = json.loads(clean_content)
    except json.JSONDecodeError as e:
        # Try to extract JSON array from content
        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end != -1:
            try:
                data = json.loads(content[start : end + 1])
            except json.JSONDecodeError:
                errors.append(f"Failed to parse JSON content: {str(e)}")
                return {}, errors
        else:
            errors.append(f"No valid JSON array found in content: {str(e)}")
            return {}, errors

    shapes: Dict[str, Dict[str, Any]] = {}

    if not isinstance(data, list):
        errors.append(f"Expected JSON array, got {type(data).__name__}")
        return {}, errors

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"Item {idx}: Expected dict, got {type(item).__name__}")
            continue

        title = item.get("title", "Untitled")
        w = item.get("w", 0)
        h = item.get("h", 0)
        xml_encoded = item.get("xml")

        if not xml_encoded:
            errors.append(f"Item {idx} ({title}): Missing 'xml' field")
            continue

        xml_str = _decode_library_xml(xml_encoded)

        try:
            try:
                root_element = ET.fromstring(xml_str)
            except ET.ParseError:
                root_element = ET.fromstring(f"<root>{xml_str}</root>")

            if root_element.tag == "mxCell":
                cells = [root_element]
            else:
                cells = list(root_element.iter("mxCell"))

            content_cells = [cell for cell in cells if not _is_structural_cell(cell)]

            if not content_cells:
                errors.append(f"Item {idx} ({title}): No valid mxCell found in XML")
                continue

            if len(content_cells) == 1:
                style = content_cells[0].get("style", "")
                shapes[title] = {
                    "baseStyle": style,
                    "width": w,
                    "height": h,
                    "xml_class": "mxCell",
                }
            else:
                cell_defs = [
                    _extract_cell_definition(cell, cell_idx)
                    for cell_idx, cell in enumerate(content_cells)
                ]
                shapes[title] = {
                    "baseStyle": _select_primary_style(cell_defs),
                    "width": w,
                    "height": h,
                    "xml_class": "mxCell",
                    "cells": cell_defs,
                }

        except ET.ParseError as e:
            errors.append(f"Item {idx} ({title}): XML parse error - {str(e)}")
        except Exception as e:
            errors.append(f"Item {idx} ({title}): Unexpected error - {str(e)}")

    return shapes, errors


def load_mxlibrary(file_path_or_url: str) -> Dict[str, Dict[str, Any]]:
    """
    Loads an mxlibrary from a file path or URL and parses it.

    Args:
        file_path_or_url: Local file path or HTTP/HTTPS URL.

    Returns:
        Dictionary of shapes.

    Raises:
        ValueError: If the file/URL cannot be loaded or parsed.
        FileNotFoundError: If the local file doesn't exist.
        urllib.error.URLError: If the URL cannot be accessed.
    """
    content = ""

    try:
        if file_path_or_url.lower().startswith(("http://", "https://")):
            try:
                with urllib.request.urlopen(file_path_or_url, timeout=30) as response:
                    content = response.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                raise ValueError(
                    f"Failed to fetch mxlibrary from URL '{file_path_or_url}': "
                    f"HTTP {e.code} - {e.reason}"
                ) from e
            except urllib.error.URLError as e:
                raise ValueError(
                    f"Failed to access URL '{file_path_or_url}': {str(e.reason)}"
                ) from e
            except Exception as e:
                raise ValueError(
                    f"Unexpected error fetching URL '{file_path_or_url}': {str(e)}"
                ) from e
        else:
            try:
                with open(file_path_or_url, "r", encoding="utf-8") as f:
                    content = f.read()
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"mxlibrary file not found: '{file_path_or_url}'"
                )
            except PermissionError:
                raise ValueError(
                    f"Permission denied reading file: '{file_path_or_url}'"
                )
            except Exception as e:
                raise ValueError(
                    f"Error reading file '{file_path_or_url}': {str(e)}"
                ) from e

        shapes, errors = parse_mxlibrary(content)

        if errors:
            logger.warning(
                f"Encountered {len(errors)} error(s) while parsing mxlibrary "
                f"from '{file_path_or_url}': {'; '.join(errors[:5])}"
                + (" ..." if len(errors) > 5 else "")
            )

        if not shapes:
            logger.warning(
                f"No valid shapes found in mxlibrary '{file_path_or_url}'. "
                f"Errors: {'; '.join(errors)}"
            )
            return {}

        return shapes

    except (ValueError, FileNotFoundError) as e:
        # Re-raise our custom errors
        raise
    except Exception as e:
        # Catch any unexpected errors
        raise ValueError(
            f"Unexpected error loading mxlibrary from '{file_path_or_url}': {str(e)}"
        ) from e
