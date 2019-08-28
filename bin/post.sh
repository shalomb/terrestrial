#!/bin/bash

jq() {
  command jq "$@" &>/dev/null
}

t() {
  job=$( http POST                       \
       http://localhost:5000/api/v1/lb   \
       configuration:=@tmp/config.json   \
       placement:=@tmp/lb.json           \
       openstack_auth:=@tmp/openrc.json  \
       configuration_type=EXTENDED
  )

  command jq -S '.' <<<"$job"
  job_url=$(command jq -cer '.job.url' <<<"$job")

  while :; do
    job=$(http GET "$job_url")
    if jq -cer '.job_status.ready == true' <<<"$job"; then
      break
    fi
    if jq -cer '.job_status.status == "ERROR"' <<<"$job"; then
      break
    fi
    command jq -cer '.job_status | {id: .id, status: .status}' <<<"$job"
    sleep 2.5
  done
  http --print HBhb --all --follow GET "$job_url"
}

k(){
  pgrep celery | xargs kill
}
