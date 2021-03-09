# Deploying with docker

This project use NGC docker image to deploy.

Please install docker-compose and docker-engine if you haven'd done so
```
./install_docker_engine.sh
```

deploying the webapp from docker-compose
```
#this comand is not production ready yet.
docker-compose up
```

After the docker finished initalization(it takes quite long first time as ngc docker image are large), you can checkout the webapp that would be running at 
[website](http://127.0.0.1:5000)