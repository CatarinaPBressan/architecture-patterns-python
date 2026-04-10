docker-build:
	docker build . -t allocations

docker-run:
	docker run -p 8000:8000 --name allocations allocations
