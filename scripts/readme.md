python setup_dynamodb.py
python manage_transformations.py list
python manage_transformations.py run JRN-SAMPLE-001 raw_analysis --triggered-by user123
python manage_transformations.py status JRN-SAMPLE-001
python manage_transformations.py jobs JRN-SAMPLE-001 raw_analysis
python manage_transformations.py download JRN-SAMPLE-001 raw_analysis JOB-001-20240115103000 schema_parsing logs
python manage_transformations.py download JRN-SAMPLE-001 raw_analysis JOB-001-20240115103000 schema_parsing reports
python run_transformation_job.py --journey-id JRN-SAMPLE-001 --stage-id raw_analysis --triggered-by user123 --reason "Testing new algorithm"
