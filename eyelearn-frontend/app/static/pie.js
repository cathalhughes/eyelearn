function pie(vars) {
    var ctx = document.getElementById("myChart").getContext('2d');
    var myPieChart = new Chart(ctx,{
    type: 'pie',
    data: {
        datasets: [{
        data: vars.data,
        backgroundColor: random_rgba(vars.data)
    }],
    labels: vars.labels,

    },
    options: {
        legend: {
            display: true,
            labels: {
                fontColor: 'rgb(0, 165, 255)'
            }
        },
        responsive: true,
        title:{
            display: true,
            text: "Number of times an activity has been played"
        }
    }
    });
}

function getRandomColor(data) {
    var letters = '0123456789ABCDEF'.split('');
    var color = '#';
    var colors = [];
    console.log("here");
    for (var j = 0; j < data.length; j++) {

        for (var i = 0; i < 6; i++ ) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        colors.push(color);
    }
    console.log(colors);
    return colors;
}

function random_rgba(data) {
    var colors = []
    for (i = 0; i < data.length; i++){

        var o = Math.round, r = Math.random, s = 255;
        colors.push('rgba(' + o(r()*s) + ',' + o(r()*s) + ',' + o(r()*s) + ',' + r().toFixed(1) + ')');
    }
    return colors;
}

module.exports = {
    getRandomColor: getRandomColor
}
