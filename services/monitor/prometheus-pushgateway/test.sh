#test add
echo "some_metric 3.14" | --data-binary @- http://pushgateway.doamin.com/metrics/job/some_job
#test add with auth
echo "some_metric 3.14" | curl -u 'test:12345' --data-binary @- http://pushgateway.doamin.com/metrics/job/some_job

#test delete
curl -X DELETE http://pushgateway.doamin.com//metrics/job/some_job

#test delete with auth
curl  -u 'test:12345' -X DELETE http://pushgateway.doamin.com//metrics/job/some_job
