'use strict';
// Pure, dependency-free evaluation utilities. Probabilities are decimals in [0, 1].
// These functions evaluate forecasts; they do not predict NFL outcomes.
function validate(rows) {
  if (!Array.isArray(rows) || rows.length === 0) throw new Error('Nonempty forecast array required');
  for (const r of rows) {
    if (!Number.isFinite(r.probability) || r.probability < 0 || r.probability > 1) throw new Error('Invalid probability');
    if (r.outcome !== 0 && r.outcome !== 1) throw new Error('Outcome must be 0 or 1');
  }
}
function evaluate(rows) {
  validate(rows);
  const epsilon = 1e-15;
  const brier = rows.reduce((s,r) => s + (r.probability-r.outcome)**2,0)/rows.length;
  const logLoss = rows.reduce((s,r) => {
    const p = Math.min(1-epsilon, Math.max(epsilon,r.probability));
    return s - r.outcome*Math.log(p) - (1-r.outcome)*Math.log(1-p);
  },0)/rows.length;
  return {count:rows.length,brier,logLoss};
}
function calibration(rows, bucketCount=10) {
  validate(rows);
  if (!Number.isInteger(bucketCount) || bucketCount < 1 || bucketCount > 100) throw new Error('Invalid bucket count');
  const buckets=Array.from({length:bucketCount},(_,i)=>({lower:i/bucketCount,upper:(i+1)/bucketCount,count:0,sumP:0,sumY:0}));
  for(const r of rows) {
    const b=buckets[Math.min(bucketCount-1,Math.floor(r.probability*bucketCount))];
    b.count++; b.sumP+=r.probability; b.sumY+=r.outcome;
  }
  return buckets.map(({lower,upper,count,sumP,sumY})=>({
    lower,upper,count,meanPredicted:count?sumP/count:null,observedRate:count?sumY/count:null
  }));
}
function breakEvenProbability(americanOdds) {
  if (!Number.isFinite(americanOdds) || Math.abs(americanOdds)<100) throw new Error('Invalid American odds');
  return americanOdds>0?100/(americanOdds+100):(-americanOdds)/((-americanOdds)+100);
}
function expectedValue(probability,americanOdds) {
  if (!Number.isFinite(probability)||probability<0||probability>1) throw new Error('Invalid probability');
  breakEvenProbability(americanOdds);
  const profit=americanOdds>0?americanOdds/100:100/(-americanOdds);
  return probability*profit-(1-probability); // net units per 1 unit wagered
}
module.exports={evaluate,calibration,breakEvenProbability,expectedValue};
