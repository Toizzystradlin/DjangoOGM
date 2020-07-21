
var ctx = document.getElementById("myChart4").getContext('2d');
var myChart = new Chart(ctx, {
	type: 'bar',
	data: {
		labels: ["{{names.0}}. {{invs_all.0}} Смен: {{shifts.0}}","{{names.1}}. {{invs_all.1}} Смен: {{shifts.1}}","{{names.2}}. {{invs_all.2}} Смен: {{shifts.2}}", "{{names.3}}. {{invs_all.3}} Смен: {{shifts.3}}", "{{names.4}}. {{invs_all.4}} Смен: {{shifts.4}}", "{{names.5}}. {{invs_all.5}} Смен: {{shifts.5}}", "{{names.6}}. {{invs_all.5}} Смен: {{shifts.6}}", "{{names.7}}. {{invs_all.7}} Смен: {{shifts.7}}", "{{names.8}}. {{invs_all.8}} Смен: {{shifts.8}}", "{{names.9}}. {{invs_all.9}} Смен: {{shifts.9}}"],
      datasets: [{
			label: 'Аварийные заявки',
			backgroundColor: "#DC143C",
			data: [12, 59, 5, 56, 58,12, 59, 87, 45],
		}, {
			label: 'Тех. обслуживание',
			backgroundColor: "#00BFFF",
			data: [12, 59, 5, 56, 58,12, 59, 85, 23],
		}],
	},
options: {
    tooltips: {
      displayColors: true,
      callbacks:{
        mode: 'x',
      },
    },
    scales: {
      xAxes: [{
        stacked: true,
        gridLines: {
          display: false,
        }
      }],
      yAxes: [{
        stacked: true,
        ticks: {
          beginAtZero: true,
        },
        type: 'linear',
      }]
    },
		responsive: true,
		maintainAspectRatio: false,
		legend: { position: 'bottom' },
	}
});