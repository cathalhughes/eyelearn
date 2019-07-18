window.onload = function() {

  document.ontouchmove = function(e){ e.preventDefault(); }

  var canvas  = document.getElementById('mycanvas');
  var canvastop = canvas.offsetTop

  var context = canvas.getContext("2d");

  var lastx;
  var lasty;

  context.strokeStyle = "#000000";
  context.lineCap = 'round';
  context.lineJoin = 'round';
  context.lineWidth = 8;


  function clear() {
    context.fillStyle = "#ffffff";
    context.rect(0, 0, 300, 300);
    context.fill();
  }

  function dot(x,y) {
    context.beginPath();
    context.fillStyle = "#000000";
    context.arc(x,y,1,0,Math.PI*2,true);
    context.fill();
    context.stroke();
    context.closePath();
  }

  function line(fromx,fromy, tox,toy) {
    context.beginPath();
    context.moveTo(fromx, fromy);
    context.lineTo(tox, toy);
    context.stroke();
    context.closePath();
  }

  function getXY(canvas, event) {
    var rect = canvas.getBoundingClientRect();  // absolute position of canvas
    return {
        x: event.touches[0].clientX - rect.left,
        y: event.touches[0].clientY - rect.top
    }
  }

  function removeFromString() {
    var string = $('#result').text();
    console.log(string);
    string = string.substring(0, string.length - 1);
    $('#result').text(string);
  }

  canvas.ontouchstart = function(event){
    event.preventDefault();
    pos = getXY(canvas, event);
//    lastx = event.touches[0].clientX;
//    lasty = event.touches[0].clientY - canvastop;
    lastx = pos.x;
    lasty = pos.y;
    dot(lastx, lasty);
  }

  canvas.ontouchmove = function(event){
    event.preventDefault();

    pos = getXY(canvas, event);
//    var newx = event.touches[0].clientX;
//    var newy = event.touches[0].clientY - canvastop;
    var newx = pos.x;
    var newy = pos.y;

    line(lastx,lasty, newx,newy);

    lastx = newx;
    lasty = newy;
  }


  var clearButton = document.getElementById('clear')
  clearButton.onclick = clear

  var removeLetterButton = document.getElementById('remove')
  removeLetterButton.onclick = removeFromString


  clear()
}
