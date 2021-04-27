/*
  overtone consonance:
    high percentage of shared overtones between scale degrees
  rational consonance:
    high percentage of rational relationships between fundamentals
  rational overtone consonance:
    high percentage of rational relationships between overtones of scale degrees
*/

var flat, natural, sharp, scaleLetters, justNoticeableDiff, maxHarmonics, absoluteThreshold;
var scale, key;
var degrees;

initialize();

$("#createkeyboard").on("click", function () {
  scale = [];
  degrees = +$("#degrees").val();
  console.log(degrees);
  buildScale();
  console.log(scale);
});

function buildKeyboard() {

}

function buildScale() {
  let note = 27.5// A0
  for (let octave = 0; octave <= 7; octave++) {
    for (let degree = 1; degree <= degrees; degree++) {
      let fundamental = 27.5*Math.pow(Math.pow(2,1/degrees),octave*degrees+degree);
      scale.push({
        letter: getScaleLetter(degree),
        octave: octave,
        degree: degree,
        fundamental: fundamental,
        overtone: getHarmonics(fundamental),
        undertone: getHarmonics(fundamental, -1)
      })
    }
  }
}

function getHarmonics(freq, direction = 1) {
  let arr = [];
  for (let i = 1; i <= maxHarmonics; i++) {
    let tone = freq*Math.pow(i,direction);
    if (tone >= thresholds.pitch.low && tone <= thresholds.pitch.high) arr.push(tone);
  }
  return arr;
}

function getScaleLetter(d) {
  let letteringMode = $("#lettermode").val();
  let arr = scaleLetters[letteringMode];
  return arr[Math.round((d-1)/degrees*arr.length)];
}

function centDiff(freq1,freq2) {
  return degrees*100*Math.log(freq1/freq2,2);
}

function isNoticeableDiff(f1,f2) {
  let diff = Math.abs(f1-f2);
  let avg = (f1+f2)/2
  return diff >= justNoticeableDiff(avg);
}

function justNoticeableDiff(f) {
  if (f < 500) return 3;
  if (f > 1000) return .6*f;
  // ref: https://www.google.com/books/edition/Springer_Handbook_of_Speech_Processing/Slg10ekZBkAC?hl=en&gbpv=1&pg=PA65&printsec=frontcover
}

function initialize() {
  flat =  "&#x266d;";
  natural = "&#x266e;";
  sharp = "&#x266f;";
  scaleLetters = {
    Equal: [`A`,`A${sharp}`,`B${flat}`,`B`,`B`,`B${sharp}`,`C${flat}`,`C`,`C`,`C${sharp}`,`D${flat}`,`D`,`D`,`D${sharp}`,`E${flat}`,`E`,`E`,`E${sharp}`,`F${flat}`,`F`,`F`,`F${sharp}`,`G${flat}`,`G`,`G`,`G${sharp}`,`A${flat}`,`A`],
    Piano: [`A`,`A${sharp}`,`B${flat}`,`B`,`B${sharp}/C${flat}`,`C`,`C`,`C${sharp}`,`D${flat}`,`D`,`D`,`D${sharp}`,`E${flat}`,`E`,`E${sharp}/F${flat}`,`F`,`F${sharp}`,`G${flat}`,`G`,`G`,`G${sharp}`,`A${flat}`,`A`]
  };
  thresholds = {
    pitch: {
      low: 20, // 20 Hz
      high: 5000 // 5000 Hz
    },
    diff: 5 // 5 cents (0.05 semitones) - the human ear's pitch resolution (https://en.wikipedia.org/wiki/Just-noticeable_difference)
  }; // ref: http://uoneuro.uoregon.edu/wehr/coursepapers/Rasch-Plomp.html
 
  maxHarmonics = 32; // also max denominator of rational consonances, includes everything up to tritones
}