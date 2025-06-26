from flask import Blueprint, jsonify, request, send_file, current_app
from io import BytesIO

fetch_api = Blueprint("fetch_api", __name__, url_prefix="/api")

@fetch_api.route("/send_webapp_id", methods=["POST"])
def update_config():
    data_service = current_app.data_service
    result = data_service.update_config(request.get_json())
    return jsonify(result)
    
@fetch_api.route("/train_model", methods=["POST"])
def train_model():
    data_service = current_app.data_service
    result = data_service.train_model(request.get_json())
    return jsonify(result)

@fetch_api.route("/deploy_model", methods=["POST"])
def deploy_model():
    data_service = current_app.data_service
    result = data_service.deploy_model(request.get_json())
    return jsonify(result)
    
@fetch_api.route("/get_latest_mltask_params", methods=["POST"])
def get_latest_mltask_params():
    data_service = current_app.data_service
    result = data_service.get_latest_mltask_params(request.get_json())
    return jsonify(result)

@fetch_api.route("/variables", methods=["POST"])
def get_variables():
    data_service = current_app.data_service
    result = data_service.get_variables(request.get_json())
    return jsonify(result)

@fetch_api.route("/models", methods=["GET"])
def get_models():
    data_service = current_app.data_service
    result = data_service.get_models()
    return jsonify(result)

@fetch_api.route("/predicted_base", methods=["POST"])
def get_predicted_base():
    data_service = current_app.data_service
    result = data_service.get_predicted_base(request.get_json())
    return jsonify(result)

@fetch_api.route("/base_values", methods=["POST"])
def get_base_values():
    data_service = current_app.data_service
    result = data_service.get_base_values(request.get_json())
    return jsonify(result)

@fetch_api.route("/lift_data", methods=["POST"])
def get_lift_data():
    data_service = current_app.data_service
    result = data_service.get_lift_data(request.get_json())
    return jsonify(result)

@fetch_api.route("/relativities", methods=["POST"])
def get_relativities():
    data_service = current_app.data_service
    result = data_service.get_relativities(request.get_json())
    return jsonify(result)

@fetch_api.route("/get_variable_level_stats", methods=["POST"])
def get_variable_level_stats():
    data_service = current_app.data_service
    result = data_service.get_variable_level_stats(request.get_json())
    return jsonify(result)
    
@fetch_api.route("/get_model_metrics", methods=["POST"])
def get_model_metrics():
    data_service = current_app.data_service
    result = data_service.get_model_metrics(request.get_json())
    return jsonify(result)

@fetch_api.route('/export_model', methods=['POST'])
def export_model():
    data_service = current_app.data_service
    csv_data = data_service.get_model_metrics(request.get_json())
    csv_io = BytesIO(csv_data)
    # Serve the CSV file for download
    return send_file(
        csv_io,
        mimetype='text/csv',
        as_attachment=True,
        download_name='model.csv'
    )

@fetch_api.route('/export_variable_level_stats', methods=['POST'])
def export_variable_level_stats():
    data_service = current_app.data_service
    csv_data = data_service.export_variable_level_stats(request.get_json())
    csv_io = BytesIO(csv_data)
    # Serve the CSV file for download
    return send_file(
        csv_io,
        mimetype='text/csv',
        as_attachment=True,
        download_name='variable_level_stats.csv'
    )

@fetch_api.route('/export_one_way', methods=['POST'])
def export_one_way():
    data_service = current_app.data_service
    csv_data = data_service.export_one_way(request.get_json())
    csv_io = BytesIO(csv_data)
    # Serve the CSV file for download
    return send_file(
        csv_io,
        mimetype='text/csv',
        as_attachment=True,
        download_name='one_way_variable.csv'
    )

@fetch_api.route("/get_excluded_columns", methods=["GET"])
def get_excluded_columns():
    data_service = current_app.data_service
    result = data_service.get_excluded_columns()
    return jsonify(result)

@fetch_api.route("/get_dataset_columns", methods=["GET"])
def get_dataset_columns():
    data_service = current_app.data_service
    result = data_service.get_dataset_columns()
    return jsonify(result)