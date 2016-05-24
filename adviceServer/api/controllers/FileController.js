/**
 * FileController
 *
 * @description :: Server-side logic for managing files
 * @help        :: http://maangalabs.com/blog/2014/08/12/uploading-a-file-in-sails/
 */

 module.exports = {

	download: function (req, res){

	 	req.validate({
	 		fd: 'string'
	 	});

	 	console.log("Request to download " + req.param("fd"))

	    var SkipperDisk = require('skipper-disk');
	    var fileAdapter = SkipperDisk(/* optional opts */);

	    // Stream the file down
	    fileAdapter.read(req.param("fd")).on('error', function (err){
	    	return res.serverError(err);
	    })
	    .pipe(res);
		
	}
};

