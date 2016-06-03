/**
 * QuestionController
 *
 * @description :: Server-side logic for managing questions
 * @help        :: See http://sailsjs.org/#!/documentation/concepts/Controllers
 */

module.exports = {

	// Empty POST request with file under field name "recording"
	// Takes the file, saves it and creates a new database question
	// referencing it.
	upload: function (req, res) {

		var mkdirp = require('mkdirp');
		var assetsDir = process.cwd() + '/assets/';
		var saveDir = assetsDir + 'questions';

		mkdirp(saveDir, function(err) { 

		    // path exists unless there was an error
		    req.file('recording').upload({
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

				Question.create({

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
	},

	// GET Unanswered questions from the server.
	getNew : function (req, res) {

		Question.find().where({ "answered" : false }).exec(function(findErr, questions)
		{
			if(findErr)
			{
				sails.log.error("question/getNew error: " + JSON.stringify(findErr))
				return res.json(401, {"err": JSON.stringify(findErr)});
			}

			return res.json(200, questions);
		});

	},
	
	// Mark the given question as answered without uploading advice
	dismiss : function(req, res) {

		Question.update({ "id" : req.param("questionId")}, {"answered" : true})
		.exec(function (err, updated)
		{
			if(err)
			{
				sails.log.error("question/dismiss error: " + JSON.stringify(err))
				return res.json(401, {"err": JSON.stringify(err)});
			}

			return res.json(200, updated);
		})

	}
};

