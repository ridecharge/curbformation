all: build test clean

build:
	ansible-galaxy install -r requirements.yml -f
	docker build -t curbformation-test .

test:
	docker run curbformation-test

nose:
	nosetests --with-coverage --cover-inclusive --cover-package=cf

clean:
	docker rmi -f curbformation-test
	rm -r roles