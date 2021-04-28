/*
  overtone consonance:
    high percentage of shared overtones between scale degrees
  rational consonance:
    high percentage of rational relationships between fundamentals
  rational overtone consonance:
    high percentage of rational relationships between overtones of scale degrees
*/

var flat, natural, sharp, halfflat, halfsharp, scaleLetters, justNoticeableDiff, maxHarmonics, absoluteThreshold;
var scale, key;
var degrees, tolerance;

initialize();

$("#createkeyboard").on("click", function () {
  scale = [];
  degrees = +$("#degrees").val();
  maxDistance = +$("#maxdistance").val();
  console.log(degrees);
  buildScale();
  computeConsonance();
  console.log(scale);
});

function buildKeyboard() {

}

function buildScale() {
  let note = 27.5// A0
  for (let octave = 0; octave <= 7; octave++) {
    for (let degree = 0; degree < degrees; degree++) {
      let fundamental = 27.5*Math.pow(Math.pow(2,1/degrees), absoluteKey(octave,degree));
      scale.push({
        letter: getScaleLetter(degree),
        octave: octave,
        degree: degree,
        fundamental: fundamental,
        harmonics: getHarmonics(fundamental),
      })
    }
  }
}

function absoluteKey(octave, degree) {
  return octave * degrees + degree;
}

function getHarmonics(freq) {
  let obj = {};
  for (let i = 0; i <= maxHarmonics; i++) {
    let overtone = freq*(i+1);
    let undertone = freq/(i+1);
    if (overtone >= thresholds.pitch.low && overtone <= thresholds.pitch.high) obj[parseInt(i).toString()] = overtone;
    if (undertone >= thresholds.pitch.low && undertone <= thresholds.pitch.high) obj[parseInt(-i).toString()] = undertone;
  }
  return obj;
}

function getScaleLetter(d) {
  let letteringMode = $("#lettermode").val();
  let arr = scaleLetters[letteringMode];
  let index = Math.round(d/degrees*arr.length) % arr.length;
  return arr[index];
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

function computeConsonance() {
  $.each(scale,(n1i,n1) => {
    scale[n1i].consonance = {};
    $.each(scale,(n2i,n2) => {
      if (Math.abs(n2i - n1i) > degrees * maxDistance) return true; // don't compare notes beyond the maximum distance
      // if (n1i == n2i) return true; // don't compare the same notes
      let harmonicResults = rationalComparison(n1.harmonics,n2.harmonics);
      scale[n1i].consonance[n2i] = {
        matches: harmonicResults.matches,
        score: harmonicResults.score
      };
    });
  });
}

function rationalComparison(tones1,tones2) {
  let matches = {};
  let score = 0;
  $.each(tones1,(t1k,t1) => {
    $.each(tones2,(t2k,t2) => {
      let tr = t2/t1;
      for(let d = 1; d <= maxHarmonics; d++) {
        if (Math.abs(tr*d - Math.round(tr*d)) <= ratioTolerance) {
          matches[`${t1k}:${t2k}`] = `${Math.round(tr*d)}/${d}`;
          score += 1/Math.max(Math.abs(t1k)+1,Math.abs(t2k)+1)/d;
          break;
        }
      }
    });
  });
  return {matches:matches, score:score};
}

function initialize() {
  flat =  "&#x266d;";
  natural = "&#x266e;";
  sharp = "&#x266f;";
  halfflat = `<img alt="half flat" src="//upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Llpd-%C2%BD.svg/6px-Llpd-%C2%BD.svg.png" width="6" height="16">`;
  halfsharp = `<img alt="half flat" src="//upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Arabic_music_notation_half_sharp.svg/6px-Arabic_music_notation_half_sharp.svg.png" width="6" height="16">`;
  schwa = `&#x0259;`
  scaleLetters = {
    Numeric: [0,1,2,3,4,5,6,7,8,9,10,11],
    SolfegeC: [`La`,`Li/Te`,`Ti`,`Do`,`Di/Ra`,`Re`,`Ri/Me`,`Mi`,`Fa`,`Fi/Se`,`Sol`,`Si/Le`],
    Solfege: [`Do`,`Di/Ra`,`Re`,`Ri/Me`,`Mi`,`Fa`,`Fi/Se`,`Sol`,`Si/Le`,`La`,`Li/Te`,`Ti`],
    SolfegeQuartertonal: [`Do`,`Dih`,`Di/Ra`,`Reh`,`Re`,`Rih`,`Ri/Me`,`Meh`,`Mi`,`Mih/Feh`,`Fa`,`Fih`,`Fi/Se`,`Seh`,`Sol`,`Sih`,`Si/Le`,`Leh`,`La`,`Lih`,`Li/Te`,`Teh`,`Ti`,`Tih/Deh`], 
    SolfegeCQuartertonal: [`La`,`Lih`,`Li/Te`,`Teh`,`Ti`,`Tih/Deh`,`Do`,`Dih`,`Di/Ra`,`Reh`,`Re`,`Rih`,`Ri/Me`,`Meh`,`Mi`,`Mih/Feh`,`Fa`,`Fih`,`Fi/Se`,`Seh`,`Sol`,`Sih`,`Si/Le`,`Leh`], // https://nmbx.newmusicusa.org/getting-your-hands-dirty-performing-microtonal-choral-music-part-2/
    Sharps: [`A`,`A${sharp}`,`B`,`C`,`C${sharp}`,`D`,`D${sharp}`,`E`,`F`,`F${sharp}`,`G`,`G${sharp}`],
    Flats: [`A`,`B${flat}`,`B`,`C`,`D${flat}`,`D`,`E${flat}`,`E`,`F`,`G${flat}`,`G`,`A${flat}`],
    Piano: [`A`,`A${sharp}/B${flat}`,`B`,`C`,`C${sharp}/D${flat}`,`D`,`D${sharp}/E${flat}`,`E`,`F`,`F${sharp}/G${flat}`,`G`,`G${sharp}/A${flat}`],
    Quartertonal: [`A`,`A${halfsharp}`,`A${sharp}/B${flat}`,`B${halfflat}`,`B`,`B${halfsharp}/C${halfflat}`,`C`,`C${halfsharp}`,`C${sharp}/D${flat}`,`D${halfflat}`,`D`,`D${halfsharp}`,`D${sharp}/E${flat}`,`E${halfflat}`,`E`,`E${halfsharp}/F${halfflat}`,`F`,`F${halfsharp}`,`F${sharp}/G${flat}`,`G${halfflat}`,`G`,`G${halfsharp}`,`G${sharp}/A${flat}`,`A${halfflat}`]
  };
  thresholds = {
    pitch: {
      low: 20, // 20 Hz
      high: 5000 // 5000 Hz
    },
    diff: 5 // 5 cents (0.05 semitones) - the human ear's pitch resolution (https://en.wikipedia.org/wiki/Just-noticeable_difference)
  }; // ref: http://uoneuro.uoregon.edu/wehr/coursepapers/Rasch-Plomp.html
  
 
  maxHarmonics = 32; // also max denominator of rational consonances, includes everything up to tritones  
  ratioTolerance = 1/(maxHarmonics+1);
}