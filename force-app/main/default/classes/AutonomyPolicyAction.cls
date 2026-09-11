public with sharing class AutonomyPolicyAction {
 public class Request { @InvocableVariable(required=true) public String policyName; @InvocableVariable(required=true) public String version; @InvocableVariable(required=true) public Integer labeledCases; @InvocableVariable(required=true) public Integer unsafeCases; }
 public class Result { @InvocableVariable public String mode; @InvocableVariable public String reason; @InvocableVariable public Boolean automaticPromotion; }
 @InvocableMethod(label='Check Case Autonomy Review Gate' description='Version-bound evidence floor; review recommendation only, not a statistical safety certificate.')
 public static List<Result> evaluate(List<Request> requests) {List<Result> out=new List<Result>(); for(Request r:requests) { Result v=new Result(); v.mode='HOLD'; v.automaticPromotion=false; v.reason='Missing policy or invalid evidence';
  Case_Autonomy_Policy__mdt p=r==null || String.isBlank(r.policyName)?null:Case_Autonomy_Policy__mdt.getInstance(r.policyName);
  if(p!=null && p.Enabled__c && p.Minimum_Cases__c!=null && p.Minimum_Cases__c>0 && !String.isBlank(r.version) && p.Configuration_Version__c==r.version && r.labeledCases!=null && r.unsafeCases!=null && r.labeledCases>=p.Minimum_Cases__c && r.unsafeCases==0) {v.mode='OWNER_REVIEW'; v.reason='Evidence floor met; subgroup validation and owner decision still required';} out.add(v);} return out; }
}
