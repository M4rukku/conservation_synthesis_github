//connect to the socket server.(assume the document.domain is the same as the server address)
var socket = io.connect('http://' + document.domain + ':' + location.port + '/sync');

initSocketIO = function() {
    //receive details from server
    socket.on('download_update', function (msg) {
        //debug purpose logging
        console.log("Received download_update" + msg.download_stats);

        var percentage = msg.download_stats.toString();
        $("#download").attr("style", "width:" + percentage + "%").attr("aria-valuenow", percentage).text(percentage + "%").html();
    });

    socket.on('classification_update', function (msg) {
        //debug purpose logging
        console.log("Received classification_update" + msg.classification_stats);

        var percentage = msg.classification_stats.toString();
        $("#classification").attr("style", "width:" + percentage + "%").attr("aria-valuenow", percentage).text(percentage + "%");
    });

    socket.on('finished_update', function (msg) {
        //debug purpose logging
        console.log("Received finished_update" + msg.finished_stats);

        var finished = (msg.finished_stats === 'true');
        $("#finished").text("Finished").removeClass("btn-secondary").addClass("btn-info");
    });
}

initSocketIO()