.PHONY: clean reinstall build release

clean:
	rm -rf build dist src/*.egg-info
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '.DS_Store' -type f -delete

reinstall:
	pip3 uninstall showroom-recorder -y
	pip3 install .

build:
	python3 -m build

release:
	./scripts/release.sh $(VERSION)
