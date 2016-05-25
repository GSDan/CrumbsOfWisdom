/**
 * AdviceController
 *
 * @description :: Server-side logic for managing advice
 * @help        :: See http://sailsjs.org/#!/documentation/concepts/Controllers
 */

module.exports = {

	// POST request with file under field name "image" and a question's ID
	// Takes the file, saves it and creates a new database Advice
	// referencing it.
	upload: function (req, res) {

		var mkdirp = require('mkdirp');
		var assetsDir = process.cwd() + '/assets/';
		var saveDir = assetsDir + 'advice';

		mkdirp(saveDir, function(err) { 

		    // path exists unless there was an error
		    req.file('image').upload({
				// don't allow the total upload size to exceed ~10MB
				maxBytes: 10000000,
				dirname: saveDir
			},function whenDone(err, uploadedFiles) {

				if (err) {
					return res.negotiate(err);
				}
					
				// If no files were uploaded, respond with an error.
				if (uploadedFiles.length === 0){
					return res.badRequest('No file was uploaded');
				}
				
				var fileAdd = uploadedFiles[0].fd.replace(assetsDir, "");

				Advice.create({
					originalQ : req.param("questionId"),
					filename : fileAdd
				}).exec(function (err){

				  	if (err) return res.negotiate(err);
				  	result = {
			    		"fd" : fileAdd
			    	}

			    	return res.json(result);

				});
			});
		});
	}
};

