import argparse, json, os, platform, sqlite3, subprocess, sys, tarfile, yaml

SDK_API_REPO_URL = 'https://github.com/MicrosoftDocs/sdk-api.git'
SDK_API_REPO_DEFAULT_LOCATION = 'sdk-api'
DOCFX_OUTPUT = 'Direct3D12.docset/Contents/Resources/Documents'

SDK_API_D3D12_RELATIVE_OUTPUT = 'windows/win32/api/d3d12'

CONTENTS_FOLDER = 'Direct3D12.docset/Contents'
RESOURCES_FOLDER = os.path.join(CONTENTS_FOLDER, 'Resources')
DOCS_FOLDER = os.path.join(RESOURCES_FOLDER, 'Documents')
DB_PATH = os.path.join(RESOURCES_FOLDER, 'docSet.dsidx')

def clone_repo(url, reporoot):
    result = subprocess.call("git clone --depth 1 {} {}".format(url, reporoot))
    return result == 0

def modify_docfx(reporoot):
    docfx_path = os.path.join(reporoot, 'sdk-api-src/content/docfx.json')
    output_filename = os.path.join(reporoot, 'sdk-api-src/content/d3d12.docfx.json')
    with open(docfx_path, 'r') as infile, open(output_filename, 'w') as outfile:
        data = json.load(infile)
        data['build']['content'][0]['files'] = [ '**/d3d12/*.md', '**/d3d12/*.yml' ]
        data['build']['resource'][0]['files'] = [ '**/d3d12/*.png', '**/d3d12/*.jpg', '**/d3d12/*.gif' ]
        json.dump(data, outfile)

    return output_filename

def run_docfx(docfx_exe, reporoot, docfx, output_directory):
    cwd = os.getcwd()
    docfx = os.path.abspath(docfx)
    output_directory = os.path.abspath(output_directory)
    result = False
    try:
        os.chdir(reporoot)
        cmd = '{} build "{}" -o "{}"'.format(docfx_exe, docfx, output_directory)
        print('Running {}'.format(cmd))
        result = subprocess.call(cmd) == 0
    finally:
        os.chdir(cwd)

    return result

def create_docset(reporoot):
    # Create SQLite db
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    try:
        cursor.execute('DROP TABLE searchIndex;')
    except:
        pass

    cursor.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
    cursor.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')

    create_docset_entries(reporoot, cursor)

    connection.commit()
    connection.close()

def create_docset_entries(reporoot, cursor):
    # for each md file; parse yaml for metadata, determine corresponding html, insert into db
    basepath = os.path.join(reporoot, 'sdk-api-src/content/d3d12')
    for source in os.listdir(basepath):
        # We only want to process documentation pages for actual API entities
        if source == 'index.md' or source == 'images':
            continue

        fullpath = os.path.join(basepath, source)
        with open(fullpath, encoding='utf-8') as f:
            contents = f.read()
            yaml_contents = contents.split("---")[1]
            yaml_contents = yaml.load(yaml_contents, Loader=yaml.SafeLoader)

            api_name = yaml_contents['api_name'][0]

            # The filename prefix indicates the "type" of the documentation
            # We use the filename prefix instead of 'api_type' from the yaml metadata because
            # the 'api_type' is misleading, the only values in d3d12 are 'DllExport', '<TBD>', 'COM', and 'HeaderDef'.
            PREFIX_TO_TYPE = {
                "ne": "Enum",
                "nf": "Function",
                "nn": "Method",
                "ns": "Struct"
            }
            prefix = source.split('-')[0]
            type = PREFIX_TO_TYPE[prefix]
            if type == None:
                os.write(2, "Unknown type prefix '{}'".format(type))
                type = 'Unknown'

            docfilename = source.replace(".md", ".html")
            docfile = SDK_API_D3D12_RELATIVE_OUTPUT + "/" + docfilename

            cursor.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?,?,?)', (api_name, type, docfile))


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--repo', action='store', default=SDK_API_REPO_DEFAULT_LOCATION,
        help='use path specified for sdk-api repo')
    argparser.add_argument('--clone', action='store_true',
        help='clone the sdk-api repo before processing')
    argparser.add_argument('--docfx', action='store_true',
        help='generate the documentation pages')
    argparser.add_argument('--docfx-exe', action='store', default='docfx',
        help='path to docfx tool (if not specified docfx is assumed to be on PATH)')
    argparser.add_argument('--no-docset', action='store_true',
        help='generate the docset database')
    argparser.add_argument('--no-archive', action='store_true',
        help='create the docset archive')
    args = argparser.parse_args()

    # Clone the docs repo (if needed)
    if args.clone:
        print('Cloning {} to {}'.format(SDK_API_REPO_URL, args.repo))
        # todo check if already populated?
        if not clone_repo(SDK_API_REPO_URL, args.repo):
            sys.exit('Error cloning sdk-api repo')

    if not os.path.exists(args.repo):
        sys.exit('sdk-api repo not found, pass --clone to clone the repo or --repo to specify the repo location')

    if args.docfx:
        print('Running docfx')
        docfx = modify_docfx(args.repo)
        if not run_docfx(args.docfx_exe, args.repo, docfx, DOCFX_OUTPUT):
            sys.exit('Error running docfx')

    if not os.path.exists(DOCFX_OUTPUT):
        sys.exit('docfx output not found, pass --docfx to build')

    if not args.no_docset:
        print('Creating docset')
        create_docset(args.repo)

    if not args.no_archive:
        print('Creating archive')
        with tarfile.open('Direct3D12.tgz', 'w:gz') as tar:
            tar.add('Direct3D12.docset')

if __name__ == '__main__':
    main()
