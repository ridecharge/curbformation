all: build clean

build:
	ansible-galaxy install -r requirements.yml -f
	docker build -t curbformation .

test:
	nosetests --with-coverage --cover-inclusive --cover-package=cf

clean:
	docker rmi curbformation
	rm -r roles