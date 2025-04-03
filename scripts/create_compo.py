import argparse


def create_compo(output, directory):
    pass
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", "-d", type=str, default=None, required=False)
    parser.add_argument("--output", "-o", type=str, default=None, required=False)

    args = parser.parse_args()
    output = args.output
    directory = args.directory
    if not output:
        output = os.path.join(directory, "compo.ern")