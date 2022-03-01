# Overview
Generate a docset for Direct3D12 for use with offline documentation browsers like Dash and Zeal. Docs are based on the official Microsoft documentation.

# Generate the Docset
From repo root, run `docset.py --clone --docfx` to clone and build the docs, create the docset database, and create the docset archive. If you already have the docs cloned, specify it with `--repo`. If `docfx` is not on your PATH, specify it with `--docfx-exe`. If you don't want the database or archive to be created, pass `--no-docset` or `--no-archive`, respectively.

To install the docset, see step 5.

These are the main steps (assuming current working directory is repo root):
1. Clone the documentation source: `git clone https://github.com/MicrosoftDocs/sdk-api.git`
2. Build the documentation (https://dotnet.github.io/docfx/tutorial/docfx_getting_started.html)
    a. Edit docfx.json to only build d3d12 (much faster)
    b. Run docfx build: `docfx build <modified docfx.json> -o Direct3D12.docset/Contents/Resources/Documents`
3. Create the docset database: `python docset.py --no-archive`
4. Create the docset archive: `python docset.py --no-docset` or `tar -cvzf Direct3D12.tgz Direct3D12.docset`
5. Install the docset

    Host a temporary local webserver to serve the docset: `python -m http.server` (python3). Then, in Zeal, add the feed by going to `Tools | Docsets | Add feed` and enter path the URL to Direct3D12.xml (e.g. `http://localhost:8000/Direct3D12.xml`).

# TODO
- include other d3d12 related pages (d3d12sdklayers, d3d12shader, d3d12video)
- https://kapeli.com/docsets#improveDocset (contribute, icon, index)
- VS extension (goto functionality like VSCode extension, extract description and parameter help for IntelliSense)
- make customizable so it can generate docs based on any Microsoft documentation
- improve docpage style (text is large, formatting pretty basic)
- add sdk-api as a submodule instead of cloning
