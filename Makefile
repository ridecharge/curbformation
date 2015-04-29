all: build

build:
	docker build .

test:
	nosetests --with-coverage --cover-inclusive --cover-package=cf
