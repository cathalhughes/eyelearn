function bar(vars) {
    var ctx = document.getElementById("myChart2").getContext('2d');
    var myBarChart = new Chart(ctx,{
    type: 'bar',
    data: {
        datasets: [{
        label: "Average",
        data: vars.data,
        backgroundColor: random_rgba(vars.data)
    }],
    labels: vars.labels,

    },
    options: {
        legend: {
            display: true,
            label: 'Average',
            labels: {
                fontColor: 'rgb(0, 165, 255)'
            }
        },
        responsive: true,
        title:{
            display: true,
            text: "Average Per Activity"
        },
        scales: {
                    xAxes: [{
                            display: true,
                            scaleLabel: {
                                display: true,
                                labelString: 'Activity'
                            }
                        }],
                    yAxes: [{
                            display: true,
                            scaleLabel: {
                                display: true,
                                labelString: 'Average(%)'
                            },
                            ticks: {
                                beginAtZero: true,
                                steps: 10,
                                stepValue: 5,
                                max: 100
                            }
                        }]
                },
    }
    });
}

function random_rgba(data) {
    var colors = []
    var o = Math.round, r = Math.random, s = 255;
    for (i = 0; i < data.length; i++){


        colors.push('rgba(' + o(r()*s) + ',' + o(r()*s) + ',' + o(r()*s) + ',' + r().toFixed(1) + ')');
    }
    return colors;
}

module.exports = {
    random_rgba: random_rgba,
    bar: bar
}