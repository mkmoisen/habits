# Set up local environment

The following will create two containers, the webapp and the database.

```commandline
docker compose up
```

To initialize the database:

```
docker exec -it habits-webapp-1 bash

cd scripts
python db.py -c
```

Go here to view the application:

    http://localhost:3000

---

# Set up Elastic Beanstalk

Download the EB CLI:

```
git clone https://github.com/aws/aws-elastic-beanstalk-cli-setup.git

pip install virtualenv

# Windows
python .\aws-elastic-beanstalk-cli-setup\scripts\ebcli_installer.py
# Follow the instructions of the output to add the EB to path


# Mac
python ./aws-elastic-beanstalk-cli-setup/scripts/ebcli_installer.py
```

Deploy an EB

```
eb init -p docker habits-test

eb create habits-test
```