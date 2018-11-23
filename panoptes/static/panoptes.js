function secondsToStr(data) {
    var milliseconds = 1000 * data;

    function numberEnding(number) {
        return (number > 1) ? 's' : '';
    }
    var temp = Math.floor(milliseconds / 1000);
    var years = Math.floor(temp / 31536000);
    if (years) {
        return years + ' year' + numberEnding(years);
    }
    var days = Math.floor((temp %= 31536000) / 86400);
    if (days) {
        return days + ' day' + numberEnding(days);
    }
    var hours = Math.floor((temp %= 86400) / 3600);
    if (hours) {
        return hours + ' hour' + numberEnding(hours);
    }
    var minutes = Math.floor((temp %= 3600) / 60);
    if (minutes) {
        return minutes + ' minute' + numberEnding(minutes);
    }
    var seconds = temp % 60;
    if (seconds) {
        return seconds + ' second' + numberEnding(seconds);
    }
    return 'just now';
}

function refreshDashboard() {
    fetch('/perf_usage')
        .then(response => {
            if (response.status !== 200) {
                console.log(response);
            }
            return response;
        })
        .then(response => response.json())
        .then(parsedResponse => {
            const unpackData = (arr, key) => {
                return arr.map(obj => obj[key])
            }
            const firstTrace = {
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Dispatches',
                x: unpackData(parsedResponse, 'time'),
                y: unpackData(parsedResponse, 'count'),
                line: {
                    color: '#17BECF'
                }
            }
            const secondTrace = {
                type: "scatter",
                mode: "lines+markers",
                name: 'Duration (ms)',
                x: unpackData(parsedResponse, 'time'),
                y: unpackData(parsedResponse, 'duration'),
                line: {
                    color: '#7F7F7F'
                }
            }
            const data = [firstTrace, secondTrace];
            const layout = {
                title: 'Quantum Scheduler Activity',
                showlegend: false
            };
            perf_graph = Plotly.newPlot('perf-container', data, layout);
            return perf_graph;
        })
        .catch(error => console.log(error));
    fetch('/io_usage')
        .then(response => {
            if (response.status !== 200) {
                console.log(response);
            }
            return response;
        })
        .then(response => response.json())
        .then(parsedResponse => {
            const unpackData = (arr, key) => {
                return arr.map(obj => obj[key])
            }
            const firstTrace = {
                type: 'scatter',
                mode: 'lines+markers',
                name: 'I/O Read (Bytes)',
                x: unpackData(parsedResponse, 'time'),
                y: unpackData(parsedResponse, 'rx'),
                line: {
                    color: '#17BECF'
                }
            }
            const secondTrace = {
                type: "scatter",
                mode: "lines+markers",
                name: 'I/O Write (Bytes)',
                x: unpackData(parsedResponse, 'time'),
                y: unpackData(parsedResponse, 'tx'),
                line: {
                    color: '#7F7F7F'
                }
            }
            const data = [firstTrace, secondTrace];
            const layout = {
                title: 'I/O Activity (Socket+Files)',
                showlegend: false
            };
            io_graph = Plotly.newPlot('io-container', data, layout);
            return io_graph;
        })
        .catch(error => console.log(error));

    fetch('/top_io')
        .then(response => {
            if (response.status !== 200) {
                console.log(response);
            }
            return response;
        })
        .then(response => response.json())
        .then(parsedResponse => {
            let i = 1;
            var table = document.getElementById("top_io");
            parsedResponse.forEach(function(item) {
                var row = table.rows[i];
                row.cells[0].innerHTML = item.location;
                row.cells[1].innerHTML = item.rx;
                row.cells[2].innerHTML = item.tx;
                i++;
            });
        });
    fetch('/uptime')
        .then(response => {
            if (response.status !== 200) {
                console.log(response);
            }
            return response;
        })
        .then(response => response.json())
        .then(parsedResponse => {
            var uptime = document.getElementById("uptime");
            uptime.innerHTML = "Uptime: " + secondsToStr(parsedResponse.value);
        })
        .catch(error => console.log(error));
    fetch('/proc_usage')
        .then(response => {
            if (response.status !== 200) {
                console.log(response);
            }
            return response;
        })
        .then(response => response.json())
        .then(parsedResponse => {
            const unpackData = (arr, key) => {
                return arr.map(obj => obj[key])
            }
            const firstTrace = {
                type: 'scatter',
                mode: 'lines+markers',
                name: 'System time',
                x: unpackData(parsedResponse, 'time'),
                y: unpackData(parsedResponse, 'kernel'),
                line: {
                    color: '#17BECF'
                }
            }
            const secondTrace = {
                type: "scatter",
                mode: "lines+markers",
                name: 'User time',
                x: unpackData(parsedResponse, 'time'),
                y: unpackData(parsedResponse, 'user'),
                line: {
                    color: '#7F7F7F'
                }
            }
            const thirdTrace = {
                type: "scatter",
                mode: "lines+markers",
                name: 'Virtual Memory',
                x: unpackData(parsedResponse, 'time'),
                y: unpackData(parsedResponse, 'virtualMemorySize'),
                line: {
                    color: '#7F7F7F'
                }
            }
            const fourthTrace = {
                type: "scatter",
                mode: "lines+markers",
                name: 'Resident Memory',
                x: unpackData(parsedResponse, 'time'),
                y: unpackData(parsedResponse, 'residentSetSize'),
                line: {
                    color: '#17BECF'
                }
            }
            const cpu_data = [firstTrace, secondTrace];
            const mem_data = [thirdTrace, fourthTrace];
            const layout = {
                title: 'Total CPU Usage (%)',
                showlegend: false
            };
            const layout2 = {
                title: 'Total Memory Usage (MB)',
                showlegend: false
            };
            Plotly.newPlot('memory-container', mem_data, layout2);
            Plotly.newPlot('cpu-container', cpu_data, layout);
        })
        .catch(error => console.log(error));
    fetch('/firefox_mem_usage')
        .then(response => {
            if (response.status !== 200) {
                console.log(response);
            }
            return response;
        })
        .then(response => response.json())
        .then(parsedResponse => {
            const unpackData = (arr, key) => {
                return arr.map(obj => obj[key])
            }
            const heap = {
                type: 'scatter',
                mode: 'lines+markers',
                name: 'JS GC Heap Usage',
                x: unpackData(parsedResponse, 'time'),
                y: unpackData(parsedResponse, 'heap'),
                line: {
                    color: '#17BECF'
                }
            }
            const audio = {
                type: "scatter",
                mode: "lines+markers",
                name: 'Audio buffer',
                x: unpackData(parsedResponse, 'time'),
                y: unpackData(parsedResponse, 'audio'),
                line: {
                    color: '#7F7F7F'
                }
            }
            const video = {
                type: "scatter",
                mode: "lines+markers",
                name: 'Video Buffer',
                x: unpackData(parsedResponse, 'time'),
                y: unpackData(parsedResponse, 'video'),
                line: {
                    color: '#8F8F8F'
                }
            }
            const dom = {
                type: "scatter",
                mode: "lines+markers",
                name: 'DOM Size',
                x: unpackData(parsedResponse, 'time'),
                y: unpackData(parsedResponse, 'dom'),
                line: {
                    color: 'red'
                }
            }
            const resources = {
                type: "scatter",
                mode: "lines+markers",
                name: 'Media Resources',
                x: unpackData(parsedResponse, 'time'),
                y: unpackData(parsedResponse, 'resources'),
                line: {
                    color: 'green'
                }
            }
            const firefox_mem_data = [heap, audio, video, resources, dom];
            const layout = {
                title: 'Firefox Memory Detailed Usage',
                showlegend: false
            };
            Plotly.newPlot('firefox-memory-container', firefox_mem_data, layout);
        })
        .catch(error => console.log(error));
}