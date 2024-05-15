{ python3, runCommand, lib }:
let
  # I wish there was a better way. If the command fails, it is very hard to see 
  # that the problem is here. Perhaps there is some way to evaluate it in python
  # and reference __version__ directly?
  version = builtins.readFile (runCommand "image-tools-version" {} ''
    PYTHONPATH=${./src} ${python3}/bin/python -c 'import image_tools.version; print(image_tools.version.__version__)' > $out
  '');
  manifest = (lib.importTOML ./pyproject.toml).project;
in
python3.pkgs.buildPythonApplication {
  pname = manifest.name;
  # The version is no longer set in pyproject.toml, so we have to jump through
  # hoops to extract it from a python script.
  # version = manifest.version;
  inherit version;

  format = "pyproject";

  src = builtins.path {
    path = ./.;
    name = manifest.name;
  };

  nativeBuildInputs = with python3.pkgs; [
    setuptools
  ];

  propagatedBuildInputs = with python3.pkgs; [
    jinja2
    pyyaml
  ];
}


