# Welcome to drawpyo

Drawpyo is a Python library for programmatically generating [Draw.io](https://www.drawio.com/) charts. It enables creating a diagram object, placing and styling objects, then writing the object to a file.

# History/Justification

We love Draw.io! Compared to expensive and heavy commercial options like Visio and Miro, Draw.io's free and lightweight app allows wider and more universal distribution of diagrams. Because the files are stored in plaintext they can be versioned alongside code in a repository as documentation. The XML-based file format makes these diagrams semi-portable, and could easily be ported to other applications if Draw.io ever failed you. For these reasons, we think it's one of the best options for documentation diagrams.
 
Drawpyo started as a weekend project by Xander Cesari, who needed to generate hierarchical tree diagrams of requirement structures and was surprised to find there wasn't a single existing Python library for working with Draw.io files. Since then a growing group of [contributors](https://github.com/XMCesari/drawpyo/graphs/contributors) has added new diagram types, shape library support, and plenty of robustness and documentation improvements.

## Key Features

- **Create diagrams programmatically** - Generate Draw.io diagrams using Python code
- **Built-in shape libraries** - Access Draw.io's standard shape collections (General, Flowchart, etc.)
- **Import external libraries** - Load third-party icon sets from XML files (Azure, AWS, Google Cloud, etc.)
- **Automatic diagram types** - Generate trees, charts, and structured diagrams automatically
- **Full styling control** - Customize colors, fonts, borders, and effects
- **Load and modify** - Import existing Draw.io files and modify them programmatically

# The Future of Drawpyo

We’re constantly working to add new functionality, address issues and feature requests. If you find Drawpyo useful and would like to contribute, we’d greatly appreciate your help! You can reach out directly at [xander@xmcesari.engineer](mailto:xander@xmcesari.engineer) or join the conversation through GitHub issues.
