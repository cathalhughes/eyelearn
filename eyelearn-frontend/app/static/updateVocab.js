var i = 5;
function updateTable(data){
  var HTML = "";
  var english = data.english;
  var translation = data.translation;
  console.log(english);
  console.log(i);
  var j = i + 5;
  console.log(j);
  while(i < j && i < english.length) {
    console.log("in here");
    HTML += "<tr><th scope='row'>" + english[i] + "</th> <th scope='row'>" + translation[i] + "</th></tr>";
    i++;
  }
  if(i >= english.length) {
    i = 0;
  }
  console.log(HTML);


  document.getElementById("vocab").innerHTML = HTML;
}

module.exports = {
    updateTable: updateTable
}