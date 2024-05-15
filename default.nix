{ sources ? import ./nix/sources.nix # managed by https://github.com/nmattia/niv
, nixpkgs ? sources.nixpkgs
, pkgs ? import nixpkgs {}
}:

{
  image-tools = pkgs.callPackage ./image-tools.nix {};
}
