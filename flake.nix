{
  description = "user-scanner";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    pyproject = fromTOML (builtins.readFile ./pyproject.toml);
    systems = [
      "x86_64-linux"
      "aarch64-linux"
      "x86_64-darwin"
      "aarch64-darwin"
    ];
    forAllSystems = nixpkgs.lib.genAttrs systems;
  in {
    packages = forAllSystems (
      system: let
        pkgs = import nixpkgs {inherit system;};
      in {
        default = pkgs.python312Packages.buildPythonApplication {
          pname = "user-scanner";
          version = pyproject.project.version;

          src = self;

          pyproject = true;

          build-system = with pkgs.python312Packages; [
            flit-core
          ];

          dependencies = with pkgs.python312Packages; [
            httpx
            socksio
            colorama
            h2
          ];

          pythonImportsCheck = ["user_scanner"];
        };
      }
    );

    apps = forAllSystems (system: {
      default = {
        type = "app";
        program = "${self.packages.${system}.default}/bin/user-scanner";
      };
    });

    devShells = forAllSystems (system: let
      pkgs = import nixpkgs {inherit system;};
    in {
      default = pkgs.mkShell {
        inputsFrom = [self.packages.${system}.default];
      };
    });
  };
}
