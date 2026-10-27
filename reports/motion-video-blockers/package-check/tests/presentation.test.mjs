import test from 'node:test';
import assert from 'node:assert/strict';
import {fmtUsd} from '../js/ui.js';
import {renderFlowResult} from '../js/flow-ui.js';
const manifest={runtime:{steps:[{id:'write',label:'Write',model:'vendor/primary',fallback:['vendor/fallback'],system:'inline:Notes {{research_notes}}',user_template:'inline:{{steps.extract.output}}'},{id:'check',label:'Check',model:'vendor/check',system:'inline:Check',user_template:'inline:{{steps.write.output}}'}],output:{show:['write.email','write.follow_ups','check.issues']}}};
const context=()=>({status:'done',estCost:.007,research_notes:'Fictional notes',steps:{write:{status:'done',output:'{"email":"raw"}',json:{email:{subject:'Hello',body:'<script>unsafe</script>'},follow_ups:[{send_after_days:3,body:'First'},{send_after_days:7,body:'Second'}]},attempts:[]},check:{status:'done',json:{verdict:'pass',issues:[]},output:'{"verdict":"pass"}',attempts:[]}}});
test('cost formatting uses normal decimals and preserves unknown values',()=>{
 assert.equal(fmtUsd(.007),'0.7¢');
 assert.equal(fmtUsd(.00000001),'<0.01¢');
 assert.equal(fmtUsd(.0004348626831),'0.043¢');
 for(const n of [.00000001,.0007,.007,.07,1.5])assert.doesNotMatch(fmtUsd(n),/e[-+]\d/i);
 assert.equal(fmtUsd(null),'—');assert.equal(fmtUsd(NaN),'—');
});
test('audit pass is qualified and only a completed pass; fix issues escaped, failed/skipped/unknown are not checked',()=>{
 let ctx=context();let html=renderFlowResult(manifest,ctx);
 assert.match(html,/AI check passed — review before sending/);assert.match(html,/model audit/i);
 assert.doesNotMatch(html,/>Fact-checked</);assert.doesNotMatch(html,/<script>/);assert.match(html,/Follow-up 2/);
 ctx.steps.check.json={verdict:'fix',issues:[{where:'body',problem:'<img> invented claim',fix:'Remove it'}]};html=renderFlowResult(manifest,ctx);
 assert.match(html,/Check found issues/);assert.match(html,/&lt;img&gt; invented claim/);
 for(const status of ['failed','skipped','waiting']){ctx.steps.check.status=status;ctx.steps.check.json={verdict:'pass'};assert.match(renderFlowResult(manifest,ctx),/Not checked/);}
 ctx.steps.check.status='done';ctx.steps.check.json={verdict:'unexpected'};assert.match(renderFlowResult(manifest,ctx),/Not checked/);
 ctx.status='stopped';ctx.message='Weak fit. Find a stronger signal before writing.';ctx.steps.write.status='skipped';
 html=renderFlowResult(manifest,ctx);assert.match(html,/Weak fit/);assert.match(html,/next-action/);assert.match(html,/Total estimated cost: 0.7¢/);
 ctx.status='failed';ctx.error='<b>Unknown usage</b>';ctx.estCost=null;html=renderFlowResult(manifest,ctx);assert.match(html,/Not checked/);assert.match(html,/Total estimated cost: unknown/);assert.match(html,/&lt;b&gt;Unknown usage/);
});
test('Pro breakdown reveals templates, prior references, actual receipts, attempts, escaped summaries, unknown and skipped costs',()=>{
 const ctx=context();manifest.runtime.steps[0].why='Selection rationale, not a benchmark';
 ctx.steps.write.receipt={requested:'vendor/fallback'};
 ctx.steps.write.attempts=[{requested:'vendor/primary',prompt_tokens:10,completion_tokens:2,estCost:.001},{requested:'vendor/fallback',prompt_tokens:20,completion_tokens:4,estCost:null}];
 ctx.steps.check.status='skipped';
 const html=renderFlowResult(manifest,ctx);
 assert.match(html,/class="breakdown pro-only"/);assert.match(html,/vendor\/primary/);assert.match(html,/vendor\/fallback/);assert.match(html,/Fallback used/);assert.match(html,/30 → 6 tok/);assert.match(html,/estimated unknown/);
 assert.match(html,/Selection rationale, not a benchmark/);assert.match(html,/steps.extract.output/);assert.match(html,/Original prompt templates/);assert.match(html,/Run-context prompts/);assert.match(html,/Notes Fictional notes/);
 assert.match(html,/data-step-cost="check">—/);assert.doesNotMatch(html,/<script>/);
});
