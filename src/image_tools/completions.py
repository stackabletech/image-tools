from .args import build_bake_argparser


def nushell_completion(completions):
    # List of options to exclude
    excluded_options = {"--product"}

    # Collect completion lines
    # One line for each argument we support in bake
    completion_lines = []
    for completion in completions:
        if completion["long"] not in excluded_options:
            # Build the baseline
            if completion["short"]:
                line = f"  {completion['long']} ({completion['short']})"
            else:
                line = f"  {completion['long']}"

            # Add ": string" if it takes a parameter
            if completion["takes_param"]:
                line += ": string"

            # Add help text as a comment if available
            if completion["help"]:
                line += f" # {completion['help']}"

            # Append the line to the list
            completion_lines.append(line)
    completion_lines = "\n".join(completion_lines)

    script_template = f"""
module bake-completions {{
    def list_products_completions [] {{
      let output = (bake --list-products | from json)
      let products = $output | columns
      return $products
    }}

    def list_versions_completions [product] {{
      let output = (bake --list-products | from json)
      let versions = $output | get $product | each {{|version| $"($product)=($version)"}}
      return $versions
    }}

    export extern "bake" [
    {completion_lines}
      --product (-p): string@"nu-complete product" # Product to build images for. For example 'druid' or 'druid=28.0.1' to build a specific version.
    ]

    def "nu-complete product" [context: string] {{
      # This function will not currently work properly should one full product be a prefix of another product name

      # context will be something like "bake --product <something>"
      # So, after splitting it up we'll have
      # - Row 0: "bake"
      # - Row 1: "--product"
      # - Row 2: "<something>" (e.g. empty or "hb" or "hbase" or "hbase=2.6.0" or similar
      let parts = ($context | split row ' ')
      let product_specification = $parts | get 2
      let product_parts = $product_specification | split row '='
      let product = $product_parts | get 0

      let all_products = list_products_completions

      # Check if the product that was specified is already "complete" (can be found in the list of all products)
      if ($all_products | any {{ |item| $item == $product }}) {{
        list_versions_completions $product
      }} else {{
        return $all_products
      }}
    }}
}}

export use bake-completions *

"""
    print(script_template)


def print_completion(shell: str):
    completions = []
    parser = build_bake_argparser()
    for action in parser._actions:
        # Separate long and short options
        long_option = None
        short_option = None

        for option in action.option_strings:
            if option.startswith("--"):
                long_option = option
            elif option.startswith("-"):
                short_option = option

        # Determine if the argument takes a parameter
        if action.nargs == 0:
            takes_param = False
        else:
            takes_param = action.nargs is not None or action.type is not None or action.default is not None

        help = None
        if action.help:
            help = action.help.replace("\n", " ").replace("\r", "").strip()

        completions.append({"long": long_option, "short": short_option, "takes_param": takes_param, "help": help})

    if shell == "nushell":
        nushell_completion(completions)
