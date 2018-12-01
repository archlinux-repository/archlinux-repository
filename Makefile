DOCKER_DEST = archlinux-repository
DOCKER_PACKAGES = python git base base-devel

docker-build:
	docker build -t $(DOCKER_DEST) .

prepare-ssh:
	eval "$(ssh-agent -s)"
	chmod 600 ./deploy_key
	ssh-add ./deploy_key

.PHONY: docker-build prepare-ssh
