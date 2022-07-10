from .wcd_import_bot import WcdImportBot

try:
    from ... import config
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "config.py not found. Please follow the instructions in the README about how to set up the config.py file"
    )

__version__ = "2.0.0"




def main() -> None:
    wcdimportbot = WcdImportBot()
    wcdimportbot.run()


if __name__ == "__main__":
    main()