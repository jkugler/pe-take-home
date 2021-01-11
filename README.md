# pe-take-home
A project for a company rhyming with Dominant Hedge

# Overview

We are designing and deploying a cloud-based architecture for analysing 911 data.

# Setup

The following tools will be required to deploy the application:

* Docker
* Terraform v0.14.x

## Infrastructure

### Prerequisites
Make sure your AWS credentials are in the environment via the following (bash) commands:

```
export AWS_ACCESS_KEY_ID="anaccesskey"
export AWS_SECRET_ACCESS_KEY="asecretkey"
```

### Deploying
#### Creating the docker container
Change directory to the `src` directory and run

`docker build <your chosen tag> .`

You will need to push the built image to a repo accessible to your AWS instance, and set the repo
name in terraform.tfvars. Or use the image already pushed, and keep the defaults.

#### AWS Infrastructure
To run the application on AWS, change to the `terraform` directory and run the commands:
```
terraform init
terraform plan
# if all looks good
terraform apply
```
Aaand here is where I hit trouble. My EC2 instance running the container apparently takes too long
to come up, and thus the load balancer removes it from the pool. As a work around, I have comitted
the ultimate configuration management sin: I have put in a delay. :) Five minutes seems to do
the trick.

Once the `terraform apply` is done, the site should be accessible at the ELB address output as
"elb_dns_name" by Terraform after about a minute.

## Notes to the Reviewer
Being a "sample project" there are of course many things that were not built out as fully as I would
have liked to. Many things would have been done differently, or more in depth, in a production
environment. These include (but are not limited to):

* DATABASE! A real database server, not a local SQLite DB. Ideally, an Amazon RDS or Aurora instance.
* DATABASE SCHEMA! A fully-fleshed application would be using a proper DB schema with one -> many
  associations for incident -> apparatus. Storing JSON blobs (when the schema is stable) is
  bad, and I feel bad.
* Proper JSON schema. It was not clear whether the data would be uploaded as a JSON *file* or as
  data in a JSON schema. That is, file upload vs. JSON REST API. That would need to be clarified
  before going to production of course. The readme said "as a JSON," which didn't help in
  disambiguating. :) It is assumed the files could be sent to the server as application/json,
  thus the server receives them as JSON docs.
  * Side note: I've been playing with Flask RestX recently (https://flask-restx.readthedocs.io/) it
    would be fun crate a model for this JSON in schema using that.
* The docker container could have been deployed in EKS, or even as a Lambda deployment to talk
  to the back-end database. There is nothing (yet) about this application which requires persistent
  instances. I will freely admit to not having any Kubernetes experience, nor any AWS/EKS experience.
  I did a LOT of reading on setting up EKS and deploying to it, but chose the solution I did because
  I wanted to take more time to understand EKS, and not just copy/paste code that worked,
  and was possibly very fragile because of my lack of understanding.
* SECURITY! This application currently has no authn/authz mechanisms.
* SSL. A production system would have an SSL cert in place.
* Remote state. This would be using remote, shared, state for Terraform in a production environment. :)
* This has a working API...but has no front-end, except for the built-in API browser. I will freely
  admit that front-end work is *not* my strong suit, and I have done very little of it.
* Properly formed JSON error messages would probably be a good addition as well.

RANT

t2.micro instances are JUNK. They are in the free tier, so I tried using that. I must have burned
at least an hour, maybe two hours,trying to figure out why it wasn't working. No response in the
local connection screen (web ssh). Then I switched to t2.medium...and it came right up. Grrr...

END RANT
