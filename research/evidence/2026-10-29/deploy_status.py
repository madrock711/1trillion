import json,pathlib,subprocess
P=pathlib.Path(__file__).parent
v=json.loads(subprocess.check_output(['aws','amplify','get-job','--app-id','d2pg7r2qjjb9u9','--branch-name','main','--job-id','706','--region','us-east-1','--query','job.summary'],text=True,encoding='utf-8'))
if v['status']=='SUCCEED':(P/'amplify-content.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(v['status'],v.get('endTime',''))
