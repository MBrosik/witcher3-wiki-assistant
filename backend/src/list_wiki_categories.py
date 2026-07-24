import mwclient

WIKI_URL = "witcher.fandom.com"
WIKI_PATH = "/"


def main() -> None:
    site = mwclient.Site(WIKI_URL, path=WIKI_PATH)
    print(f"Connected to {site.host}")
    print("site.categories:")
    for category in site.categories:
        print(f"  {category.name}")


if __name__ == "__main__":
    main()
