from src.cli.main import main


def lambda_handler(event: dict, _):
    print('Hello world!')


if __name__ == '__main__':
    main()
