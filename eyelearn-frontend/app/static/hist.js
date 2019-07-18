function hist(vars) {
    var ctx = document.getElementById("myChart1").getContext('2d');
        var myChart = new Chart(ctx, {
          type: 'bar',
          data: {
        labels: [20, 40, 60, 80, 100],
        datasets: [{
          label: 'Class: ' + vars.classcode,
          data: organiseData(vars.data),
          backgroundColor: 'rgba(0, 165, 255)',
        }]
          },
          options: {
        scales: {
          xAxes: [{
            display: false,
            barPercentage: 1.3,
            ticks: {
                max: 3,
            }
         }, {
            display: true,
            scaleLabel: {
                display: true,
                labelString: 'Score(%)'
            },
            ticks: {
                autoSkip: false,
                max: 4,
            }
          }],
          yAxes: [{
            display: true,
            scaleLabel: {
                display: true,
                labelString: 'Count'
            },
            ticks: {
              beginAtZero:true
            }
          }]
        },
        responsive: true,
        title:{
//            display: true,
//            text: "Distribution of class averages"
        }
          }
        });
}

function organiseData(data){
    var count = [0, 0, 0, 0, 0, 0];
    for(i = 0; i < data.length; i++) {
        console.log(data[i]);
        if(data[i] < 20) {
            count[0] += 1;
        } else if(data[i] < 40) {
            count[1] += 1;
        } else if(data[i] < 60) {
            count[2] += 1;
        } else if(data[i] < 80) {
            count[3] += 1;
        } else {
            count[4] += 1;
        }

    }
    console.log(count);
    return count;
}

module.exports = {
    organiseData: organiseData
}