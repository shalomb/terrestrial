# terrestrial

Proof-of-Concept: Thin REST API shim for your existing terraform + ansible IaC
codebase.

## Use Cases

- IaaS/PaaS. Exposing IaC code projects over REST APIs such that instances
(your IaC deliverables) can be created, managed, lifecycled, etc. e.g. Port
your Terraform + Ansible that manages PostgreSQL clusters into Terrestrial and
realize your Database-as-a-Service.
- Defining custom operational and system boundaries around IaC. e.g. Use
Terrestrial + $your_favourite_reverse_proxy in place of Gitlab hacked-up
pipelines to manage infrastructure.

# Goals

- Provide a thin "API Service" layer around any (within reason) Terraform and/or
  Ansible IaC codebase to realize a X-as-a-Service offering. Define a nominal
  interface the hosted IaC codebase should implement to be Onboarded into
  Terrestrial.
- Provide a full CRUD Interface using established REST patterns (e.g.
  [POST-PUT](http://restalk-patterns.org/post-put.html) to allow long-running
  terraform/ansible processes to create the technical resource).
- Easy deployment: Build a docker image containing the complete bundle of
  Terrestrial + IaC code to deploy the "service". Allow sourcing of IaC projects
  from remote git repositories.
- Dynamic Inventory: Refactor [shalomb/tofu](https://github.com/shalomb/tofu)
  to provide a dynamic inventory of terraform resources to ansible, etc.
- Allow for integrations into load-balancers/reverse-proxies/ADCs to augment
  system and operational needs. Support for OAuth/OIDC/Logging.

## HOWTO

A write-up required but see scripts in `bin/` to get started.

## IaC Interface

TODO: This section is incomplete.

- Use `tfvars.json` to pass resource attributes as variables from terrestrial
  to terraform.
- Use `terraform outputs` from terraform to state created resources.
- Use the `terraform state` to describe the full IaC inventory to technologies
  further up the stack (e.g. ansible, etc).
- Use `group_vars/all` to pass resource attributes as variables to ansible.
- Use JSON outputs to capture output from terraform's `plan`, `apply`, `destroy`,
  etc.
- Use custom callbacks (and so JSON) to capture output from ansible playbook runs.

