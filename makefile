reinstall:
	pip3 uninstall showroom-recorder -y; pip3 install .

upload:
	rm -rf dist
	python3 -m build
	twine upload dist/*