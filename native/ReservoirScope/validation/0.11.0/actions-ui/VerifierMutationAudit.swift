import Foundation
import EssentialsCore
final class Store: ActionJournalStore, @unchecked Sendable {
 var entries:[String:JournalEntry]=[:]; let failLeft:Bool
 init(_ failLeft:Bool=false) {self.failLeft=failLeft}
 func save(_ e:JournalEntry,arm:ActionArm)throws->JournalSaveReceipt {
  if failLeft && arm == .left { throw EssentialsError.invalid("Controlled left save failure") }
  entries[arm.rawValue+e.id]=e
  return JournalSaveReceipt(status:.saved,entryID:e.id,sha256:e.sha256,relativePath:arm.rawValue+"/"+e.id+".json")
 }
 func read(entryID:String,arm:ActionArm)throws->JournalEntry {entries[arm.rawValue+entryID]!}
}
func object(_ r:ActionComparisonRecord)throws->[String:Any] { try JSONSerialization.jsonObject(with:JSONEncoder().encode(r)) as! [String:Any] }
func decode(_ o:[String:Any])throws->ActionComparisonRecord { try JSONDecoder().decode(ActionComparisonRecord.self,from:JSONSerialization.data(withJSONObject:o)) }
func attempt(_ name:String,_ o:[String:Any]) { do {_ = try decode(o).verify(); print("ACCEPTED: " + name)} catch {print("REJECTED: " + name + " — " + error.localizedDescription)} }
@main struct Audit {
 static func main()async throws {
  let spec=ActionComparisonSpecification(stage:.reservoirReturn,steps:4,turnEvery:3)
  let good=try ActionComparisonSession(specification:spec,journalStore:Store())
  _=try await good.advance(); let before=try await good.writeJournal(); let record=try await good.advance()
  var omission=try object(record), left=omission["left"] as! [String:Any]
  left["actions"]=[];left["journals"]=[];omission["left"]=left
  attempt("left manual D journal omitted from D/E pair",omission)
  let bad=try ActionComparisonSession(specification:spec,journalStore:Store(true))
  _=try await bad.advance();let failed=try await bad.writeJournal()
  var continued=try object(failed)
  continued["right"] = try object(before)["right"]!
  attempt("right saves/applies despite prior left journal-save failure",continued)
  var fakeFailure=try object(failed)
  var failLeft=fakeFailure["left"] as! [String:Any], acts=failLeft["actions"] as! [[String:Any]], action=acts[0]
  for key in ["rawReply","rawReplyByteCount","providerModel","stopReason","providerComplete","tokenCount","chosenAction","journalEntryID","saveReceipt","encodedFeatures","semanticVector","applicationStep"] {action.removeValue(forKey:key)}
  action["status"]="failed";action["failurePhase"]="language";action["failure"]="impossible fixed tape transport failure";action["requestStarted"]=false
  acts[0]=action;failLeft["actions"]=acts;failLeft["failure"]="impossible fixed tape transport failure";fakeFailure["left"]=failLeft;fakeFailure["failure"]="impossible fixed tape transport failure"
  attempt("fixed reply tape claims provider transport failure",fakeFailure)
 }
}
