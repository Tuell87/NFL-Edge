const test=require('node:test');
const assert=require('node:assert/strict');
const {evaluate,calibration,breakEvenProbability,expectedValue}=require('../evaluation/metrics.cjs');
test('perfect forecasts have zero Brier',()=>assert.equal(evaluate([{probability:1,outcome:1},{probability:0,outcome:0}]).brier,0));
test('Brier and log loss computed on known sample',()=>{
  const x=evaluate([{probability:0.75,outcome:1},{probability:0.25,outcome:0}]);
  assert.equal(x.count,2);assert.equal(x.brier,0.0625);
  assert.ok(Math.abs(x.logLoss+Math.log(0.75))<1e-12);
});
test('invalid forecasts rejected',()=>{
  assert.throws(()=>evaluate([]));assert.throws(()=>evaluate([{probability:1.2,outcome:1}]));
  assert.throws(()=>evaluate([{probability:0.4,outcome:2}]));
});
test('calibration includes probability one in final bucket',()=>{
  const x=calibration([{probability:0,outcome:0},{probability:1,outcome:1}],2);
  assert.equal(x[0].count,1);assert.equal(x[1].count,1);
  assert.equal(x[1].observedRate,1);
});
test('empty calibration buckets are explicitly null',()=>{
  const x=calibration([{probability:0.1,outcome:0}],2);
  assert.equal(x[1].observedRate,null);
});
test('American odds break-even conversions',()=>{
  assert.ok(Math.abs(breakEvenProbability(150)-0.4)<1e-12);
  assert.ok(Math.abs(breakEvenProbability(-150)-0.6)<1e-12);
});
test('expected value positive and negative',()=>{
  assert.ok(Math.abs(expectedValue(0.5,150)-0.25)<1e-12);
  assert.ok(Math.abs(expectedValue(0.5,-150)+1/6)<1e-12);
});
test('invalid odds rejected',()=>assert.throws(()=>breakEvenProbability(50)));
