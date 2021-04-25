const flat =  "&#x266d;";
const natural = "&#x266e;";
const sharp = "&#x266f;";
const actualizationTolerance = 3;
//const scaleLetters = ["A","A"+sharp,"B"+flat,"B","B","B"+sharp,"C"+flat,"C","C","C"+sharp,"D"+flat,"D","D","D"+sharp,"E"+flat,"E","E","E"+sharp,"F"+flat,"F","F","F"+sharp,"G"+flat,"G","G","G"+sharp,"A"+flat,"A"]; // equal spacing
const scaleLetters = ["A","A"+sharp,"B"+flat,"B","B"+sharp+"/C"+flat,"C","C","C"+sharp,"D"+flat,"D","D","D"+sharp,"E"+flat,"E","E"+sharp+"/F"+flat,"F","F"+sharp,"G"+flat,"G","G","G"+sharp,"A"+flat,"A"]; // piano spacing 1

var scaleSquare = [];
for (let i = 0; i < scaleLetters.length; i++) {
  for (let j = 0; j < scaleLetters.length; j++) {
    scaleSquare.push(scaleLetters[i]);
  }
}

let CPos = ((scaleSquare.length - scaleSquare.reverse().findIndex(a=>a=="C") - 1) + scaleSquare.reverse().findIndex(a=>a=="C"))/2;

console.log({scaleSquare:scaleSquare,CPos:CPos});

function centDiff(a,b,degrees) {
  return degrees*100*Math.log(a/b,2);
}

function buildScale(degrees, overUnder, octaves = 8) {
  octaves = Math.round(octaves/2)*2;
  let letterSpacing = scaleSquare.length / degrees;
  let beginningOctave = 4-(octaves/2);
  let A440 = (degrees * octaves)/2;
  var scale = {degrees:degrees,overUnder:overUnder,octaves:octaves,beginningOctave:beginningOctave,A440:A440,notes:[]};
  let key = 0;
  let octave = beginningOctave;
  for (let i = 0; i < octaves; i++) {
    for (let j = 1; j <= scaleSquare.length; j += letterSpacing) {
      let letterPos = Math.round(j)-1;
      let letter = scaleSquare[letterPos];
      let fundamental = 440*Math.pow(Math.pow(2,1/degrees),key-A440);
      if (octave == beginningOctave + i && letterPos >= CPos) octave++;
      scale.notes.push({
        letter:letter,
        octave:octave,
        name:letter+octave,
        key:key,
        fundamental:fundamental,
        overtone:[],
        undertone:[]
      });
      for (let k = 2; k <= (overUnder + 1); k++) {
        scale.notes[scale.notes.length-1].overtone.push({frequency:fundamental*k});
        scale.notes[scale.notes.length-1].undertone.push({frequency:fundamental/k});
      }
      key++;
    }
  }
  scale.actualized = 0;
  for (let i = 0; i < overUnder; i++) {
    let oFreq = scale.notes[A440].overtone[i].frequency, uFreq = scale.notes[A440].undertone[i].frequency;
    let oDiff = 0, uDiff = 0;
    let oPitch = scale.notes[scale.notes.findIndex((a)=>{
      let diff = centDiff(a.fundamental,oFreq,degrees);
      if (Math.abs(diff) <= 50) {
        oDiff = diff;
        return true;
      }
    })] || {name:"N/A"};
    let uPitch = scale.notes[scale.notes.findIndex((a)=>{
      let diff = centDiff(a.fundamental,uFreq,degrees);
      if (Math.abs(diff) <= 50) {
        uDiff = diff;
        return true;
      }
    })] || {name:"N/A"};
    oDiff = Math.round(oDiff*1000000)/1000000;
    uDiff = Math.round(uDiff*1000000)/1000000;
    scale.notes[A440].overtone[i].pitch = oPitch.name + (oDiff >= 0 ? "+" : "") + oDiff;
    scale.notes[A440].undertone[i].pitch = uPitch.name + (uDiff >= 0 ? "+" : "") + uDiff;
    actualizationTolerance >= Math.abs(oDiff) && scale.actualized++;
    actualizationTolerance >= Math.abs(uDiff) && scale.actualized++;
  }   
  return scale;
}


var scales = [];

for (let i = 2; i <=30; i++) {
  scales.push(buildScale(i,32,40));
}
console.log(scales);

let tempStr = "";
for (let i = 0; i < scales.length; i++) {
  tempStr += `<button class="btn btn-primary">${scales[i].degrees}tet <span class="badge badge-light" title="${scales[i].notes[scales[i].A440].undertone.reverse().map(a=>a.pitch)} F|F ${scales[i].notes[scales[i].A440].overtone.map(a=>a.pitch)}">${scales[i].actualized} actualized</span></button><div class="btn-group">`;
  for (let j = 0; j < scales[i].notes.length; j++) {
    let note = scales[i].notes[j];
    tempStr += `<button class="key btn btn-xs btn-${note.letter.length>1?"dark":"light"}" title="${Math.round(note.fundamental*100)/100} Hz" data-frequency="${note.fundamental}">${note.name}</button>`;
  }
  tempStr += `</div><br/>`;
}
$("#scales").html(tempStr);

$(".key").mousedown(function() {playSound(+$(this).data("frequency"),"sine")}).mouseup(function() {stopSound()});

var context = null;
var oscillator = null;
function getOrCreateContext() {
  if (!context) {
    context = new AudioContext();
    oscillator = context.createOscillator();
    oscillator.connect(context.destination);
  }
  return context;
  
}

var isStarted = false;
function playSound(frequency, type) {
  getOrCreateContext();
  oscillator.frequency.setTargetAtTime(frequency, context.currentTime, 0);
  if (!isStarted) {
    oscillator.start(0);
    isStarted = true;
  } else {
    context.resume();
  }
}

function stopSound() {
  context.suspend();
}

/*document.getElementById('basic').addEventListener('click', playSound.bind(null, 440, 'square'));
document.getElementById('basic2').addEventListener('click', playSound.bind(null, 800, 'square'));
document.getElementById('basic3').addEventListener('click', playSound.bind(null, 1000, 'square'));
document.getElementById('stop').addEventListener('click', stopSound);*/
$(document).tooltip();
