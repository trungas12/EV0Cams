# sup3rvic0 Repo

APT repository for rootless jailbroken iPhones.

## Add the source

After GitHub Pages is enabled, open the Pages URL on the iPhone and tap **Add to Sileo**, or paste that URL into Sileo/Zebra as a source.

## Publish a package update

1. Put the new `.deb` file in `debs/`.
2. Run `python generate_repo.py`.
3. Commit and push `Packages`, `Packages.gz`, `Release`, and the `.deb` file.

GitHub Pages must publish from the repository root on the default branch.
