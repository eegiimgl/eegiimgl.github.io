---
layout: default
title: "Docker long-running container logs"
date: 2020-06-12
---
Well finally I decided put some blog post how I accomplish some things over there. 

Here is example commands how we can investigate dangling docker volumes. 
```shell
docker volume ls |grep -c rancher-secrets

docker volume ls -q --filter “dangling=true” | wc -l

docker volume prune
```
