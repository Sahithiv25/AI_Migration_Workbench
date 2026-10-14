"""Reproducible synthetic legacy CRM data with injected defects and ground truth."""
from pathlib import Path
import csv, random, json, argparse
from datetime import date, timedelta

ROOT = Path(__file__).parent
FIELDS = {
 'users':['Legacy User Key','Employee Name','Work Email','Team','Enabled'],
 'accounts':['Legacy Acct ID','Client / Organization','Sector','Web Domain','Billing Country','Acct Rep'],
 'contacts':['Legacy Contact ID','Parent Account','Given Name','Surname','Email Address','Mobile'],
 'opportunities':['Deal Key','Customer Ref','Deal Owner','Pipeline Status','Contract Value','Currency Code','Expected Close'],
 'activities':['Event ID','Related Account','Related Contact','Related Deal','Interaction Type','Event Date','Performed By']
}
FIRST=['Ava','Noah','Mia','Liam','Emma','Ethan','Sofia','Arjun','Priya','Olivia','Mateo','Zoe']
LAST=['Patel','Smith','Chen','Brown','Garcia','Johnson','Williams','Kim','Shah','Davis']
WORDS=['Pioneer','Atlas','Summit','Evergreen','Meridian','Silver','Orion','Northstar','Blue','Cedar','Nova','Harbor']
SUFFIX=['Systems','Labs','Industries','Consulting','Solutions','Group']

def save(path,fields,rows):
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def build(scale=1.0,seed=42):
 r=random.Random(seed)
 counts={k:max(1,round(n*scale)) for k,n in [('users',200),('accounts',10000),('contacts',25000),('opportunities',15000),('activities',30000)]}
 out=ROOT/'data'; out.mkdir(exist_ok=True)
 truth=[]; datasets={}
 def defect(entity,row_id,kind,field,original,changed):
  truth.append({'entity':entity,'row_id':row_id,'defect_type':kind,'field':field,'original':str(original),'injected':str(changed)})
 users=[]
 for i in range(counts['users']):
  uid=f'U{i+1:06d}'; name=f'{r.choice(FIRST)} {r.choice(LAST)}'; users.append(dict(zip(FIELDS['users'],[uid,name,f'user{i+1}@atlas-example.test',r.choice(['Sales','Marketing','Success']),r.choice(['Yes','Yes','Yes','No'])])))
 datasets['users']=users
 accounts=[]
 for i in range(counts['accounts']):
  aid=f'A{i+1:07d}'; name=f'{r.choice(WORDS)} {r.choice(WORDS)} {r.choice(SUFFIX)}'; accounts.append(dict(zip(FIELDS['accounts'],[aid,name,r.choice(['Technology','Finance','Healthcare','Retail']),f'customer{i+1}.example.test',r.choice(['US','United States','USA','CA','UK']),r.choice(users)['Legacy User Key']])))
 datasets['accounts']=accounts
 contacts=[]
 for i in range(counts['contacts']):
  cid=f'C{i+1:07d}'; contacts.append(dict(zip(FIELDS['contacts'],[cid,r.choice(accounts)['Legacy Acct ID'],r.choice(FIRST),r.choice(LAST),f'contact{i+1}@example.test',f'+1-202-555-{i%10000:04d}'])))
 datasets['contacts']=contacts
 opps=[]
 for i in range(counts['opportunities']):
  oid=f'O{i+1:07d}'; dt=date(2025,1,1)+timedelta(days=r.randrange(1000)); opps.append(dict(zip(FIELDS['opportunities'],[oid,r.choice(accounts)['Legacy Acct ID'],r.choice(users)['Legacy User Key'],r.choice(['Prospecting','Qualification','Proposal','Won','Lost']),str(r.randrange(1000,500000)),r.choice(['USD','EUR','GBP']),dt.isoformat()])))
 datasets['opportunities']=opps
 acts=[]
 for i in range(counts['activities']):
  eid=f'T{i+1:07d}'; a=r.choice(accounts)['Legacy Acct ID']; c=r.choice(contacts); o=r.choice(opps); dt=date(2025,1,1)+timedelta(days=r.randrange(600)); acts.append(dict(zip(FIELDS['activities'],[eid,a,c['Legacy Contact ID'],o['Deal Key'],r.choice(['Call','Meeting','Email']),dt.isoformat(),r.choice(users)['Legacy User Key']])))
 datasets['activities']=acts
 # Defects are introduced into distinct rows per entity, retaining original values in truth.
 for entity,rows in datasets.items():
  indexes=list(range(len(rows))); r.shuffle(indexes)
  for j,idx in enumerate(indexes[:min(len(rows),max(1,int(len(rows)*.07)))]):
   row=rows[idx]; id_field=FIELDS[entity][0]; row_id=row[id_field]
   if entity=='accounts':
    field='Client / Organization' if j%3==0 else ('Acct Rep' if j%3==1 else 'Billing Country')
    kind=['missing_required','orphan_owner','format_variant'][j%3]
    new=['','U999999','U.S.A.'][j%3]
   elif entity=='contacts':
    field='Email Address' if j%3==0 else ('Parent Account' if j%3==1 else 'Mobile')
    kind=['invalid_email','orphan_account','missing_optional'][j%3]
    new=['invalid-at-example','A9999999',''][j%3]
   elif entity=='opportunities':
    field='Pipeline Status' if j%3==0 else ('Customer Ref' if j%3==1 else 'Expected Close')
    kind=['invalid_enum','orphan_account','invalid_date'][j%3]
    new=['Maybe','A9999999','2026-99-99'][j%3]
   elif entity=='activities':
    field='Event Date' if j%3==0 else ('Related Contact' if j%3==1 else 'Performed By')
    kind=['invalid_date','orphan_contact','orphan_owner'][j%3]
    new=['not-a-date','C9999999','U999999'][j%3]
   else:
    field='Work Email' if j%2==0 else 'Employee Name'; kind='invalid_email' if j%2==0 else 'missing_required'; new='not-an-email' if j%2==0 else ''
   old=row[field]; row[field]=new; defect(entity,row_id,kind,field,old,new)
 # Duplicate candidates with known linkage, without changing row count.
 for entity,field in [('accounts','Client / Organization'),('contacts','Email Address')]:
  rows=datasets[entity]; start=max(1,int(len(rows)*.93)); pairs=min(100,max(1,len(rows)//100))
  for i in range(pairs):
   src=rows[i]; dst=rows[start+i] if start+i<len(rows) else rows[-1]
   old=dst[field]; dst[field]=src[field]
   defect(entity,dst[FIELDS[entity][0]],'duplicate_candidate',field,old,dst[field])
 for entity,rows in datasets.items(): save(out/f'{entity}_legacy.csv',FIELDS[entity],rows)
 save(out/'injected_defects.csv',['entity','row_id','defect_type','field','original','injected'],truth)
 schema={'users':{'pk':'user_id','required':['user_id','full_name','email'],'foreign_keys':{}},'accounts':{'pk':'account_id','required':['account_id','account_name'],'foreign_keys':{'owner_id':'users.user_id'}},'contacts':{'pk':'contact_id','required':['contact_id','account_id','last_name'],'foreign_keys':{'account_id':'accounts.account_id'}},'opportunities':{'pk':'opportunity_id','required':['opportunity_id','account_id','stage','amount'],'foreign_keys':{'account_id':'accounts.account_id','owner_id':'users.user_id'}},'activities':{'pk':'activity_id','required':['activity_id','activity_date'],'foreign_keys':{'account_id':'accounts.account_id','contact_id':'contacts.contact_id','opportunity_id':'opportunities.opportunity_id','owner_id':'users.user_id'}}}
 (ROOT/'target_schema.json').write_text(json.dumps(schema,indent=2))
 manifest={'seed':seed,'scale':scale,'row_counts':counts,'injected_defects':len(truth),'note':'Synthetic data only. Duplicate candidate labels are heuristic test cases, not fully adjudicated entity-resolution truth.'}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
 print(json.dumps(manifest,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--scale',type=float,default=1.0);p.add_argument('--seed',type=int,default=42);args=p.parse_args();build(args.scale,args.seed)
