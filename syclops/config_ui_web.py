#!/usr/bin/env python3
"""
Syclops Config UI - Web-based version using a simple HTTP server
"""

import http.server
import socketserver
import webbrowser
import json
import yaml
import os
import sys
from urllib.parse import parse_qs, urlparse
from pathlib import Path
import tempfile
import threading
import time


class ConfigHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.config_data = {}
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_html().encode())
        elif self.path == '/config.js':
            self.send_response(200)
            self.send_header('Content-type', 'application/javascript')
            self.end_headers()
            self.wfile.write(self.get_js().encode())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/save_config':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                config_data = json.loads(post_data.decode())
                yaml_config = self.generate_yaml_config(config_data)
                
                # Save to a temporary file and provide download
                temp_dir = tempfile.mkdtemp()
                config_file = os.path.join(temp_dir, 'syclops_config.yaml')
                
                with open(config_file, 'w') as f:
                    f.write(yaml_config)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'success': True,
                    'file_path': config_file,
                    'yaml_content': yaml_config
                }
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'success': False, 'error': str(e)}
                self.wfile.write(json.dumps(response).encode())
        
        elif self.path == '/get_assets':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            assets = self.get_available_assets()
            self.wfile.write(json.dumps(assets).encode())
        
        elif self.path == '/launch_asset_browser':
            try:
                self.launch_asset_browser()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'success': True, 'message': 'Asset browser launched'}
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'success': False, 'error': str(e)}
                self.wfile.write(json.dumps(response).encode())
                
        elif self.path == '/get_assets':
            try:
                assets = self.get_available_assets()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(assets).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'success': False, 'error': str(e)}
                self.wfile.write(json.dumps(response).encode())
                
        elif self.path == '/launch_asset_browser':
            try:
                self.launch_asset_browser()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'success': True, 'message': 'Asset browser launched'}
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'success': False, 'error': str(e)}
                self.wfile.write(json.dumps(response).encode())
        
        elif self.path == '/generate_data':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                config_data = json.loads(post_data.decode())
                result = self.run_syclops_generation(config_data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'success': False, 'error': str(e)}
                self.wfile.write(json.dumps(response).encode())

    def _parse_boolean(self, value):
        """Parse boolean value from various input types"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)

    def generate_yaml_config(self, data):
        """Generate YAML config from form data"""
        config = {
            'steps': int(data.get('steps', 1)),
            'seeds': {
                'numpy': int(data.get('numpy_seed', 42)),
                'cycles': int(data.get('cycles_seed', 42))
            },
            'render_device': data.get('render_device', 'GPU'),
            'render_hardware': data.get('render_hardware', 'CUDA'),
            'denoising_enabled': self._parse_boolean(data.get('denoising_enabled', True)),
            'denoising_algorithm': data.get('denoising_algorithm', 'OPENIMAGEDENOISE'),
            
            'transformations': {
                'map': {
                    'location': [0, 0, 0],
                    'rotation': [0, 0, 0],
                    'children': {
                        'camera_link': {
                            'location': {
                                'linear': [[-8, -12, 1], [0.5, 0.5, 0.2]]
                            },
                            'rotation': {
                                'normal': [[1.3, 0, 0], [0.05, 0.05, 0.05]]
                            }
                        }
                    }
                }
            },
            
            'scene': {
                'syclops_plugin_ground': [{
                    'name': 'Ground',
                    'size': int(data.get('ground_size', 50)),
                    'texture': data.get('ground_texture', 'Example Assets/Muddy Dry Ground'),
                    'class_id': 1
                }],
                'syclops_plugin_environment': [{
                    'type': 'hdri',
                    'environment_image': {
                        'random_selection': [data.get('environment', 'Assets_own/Field')]
                    }
                }]
            },
            
            'sensor': {
                'syclops_sensor_camera': [{
                    'name': 'main_camera',
                    'frame_id': 'camera_link',
                    'resolution': [
                        int(data.get('resolution_width', 2048)), 
                        int(data.get('resolution_height', 2048))
                    ],
                    'focal_length': float(data.get('focal_length', 40)),
                    'sensor_width': float(data.get('sensor_width', 35)),
                    'exposure': float(data.get('exposure', 0.3)),
                    'gamma': float(data.get('gamma', 1.4)),
                    'outputs': {
                        'syclops_output_rgb': [{
                            'samples': 2,
                            'debug_breakpoint': True,
                            'id': 'main_cam_rgb'
                        }],
                        'syclops_output_pixel_annotation': [{
                            'semantic_segmentation': {'id': 'main_cam_semantic'},
                            'instance_segmentation': {'id': 'main_cam_instance'}
                        }]
                    }
                }]
            }
        }
        
        # Add crop plugins if any are configured
        crops_data = data.get('crops', '[]')
        if crops_data and crops_data != '[]':
            try:
                crops = json.loads(crops_data)
                if crops:
                    config['scene']['syclops_plugin_crop'] = []
                    for i, crop in enumerate(crops):
                        crop_config = {
                            'name': crop.get('name', f'crop_{i}'),
                            'models': [crop.get('model', 'Assets_own/bbch_15')],
                            'floor_object': 'Ground',
                            'crop_angle': float(crop.get('crop_angle', 0)),
                            'row_distance': float(crop.get('row_distance', 0.8)),
                            'row_standard_deviation': float(crop.get('row_standard_deviation', 0.32)),
                            'plant_distance': float(crop.get('plant_distance', 0.4)),
                            'plant_standard_deviation': float(crop.get('plant_standard_deviation', 0.2)),
                            'scale_standard_deviation': float(crop.get('scale_standard_deviation', 0.5)),
                            'class_id': int(crop.get('class_id', i + 2)),
                            'seed': int(crop.get('seed', i + 1))
                        }
                        if crop.get('class_id_offset'):
                            crop_config['class_id_offset'] = crop.get('class_id_offset')
                        
                        config['scene']['syclops_plugin_crop'].append(crop_config)
            except json.JSONDecodeError:
                pass  # Ignore invalid JSON
        
        # Add object plugins if any are configured
        objects_data = data.get('objects', '[]')
        if objects_data and objects_data != '[]':
            try:
                objects = json.loads(objects_data)
                if objects:
                    config['scene']['syclops_plugin_object'] = []
                    for i, obj in enumerate(objects):
                        obj_config = {
                            'name': obj.get('name', f'object_{i}'),
                            'models': [obj.get('model', 'Assets_own/ISO Object')],
                            'frame_id': obj.get('frame_id', 'iso_object'),
                            'class_id': int(obj.get('class_id', i + 10)),
                            'place_on_ground': obj.get('place_on_ground', 'false') == 'true'
                        }
                        
                        if obj_config['place_on_ground']:
                            obj_config['floor_object'] = obj.get('floor_object', 'Ground')
                        
                        if obj.get('max_texture_size'):
                            obj_config['max_texture_size'] = int(obj['max_texture_size'])
                        if obj.get('decimate_mesh_factor'):
                            obj_config['decimate_mesh_factor'] = float(obj['decimate_mesh_factor'])
                        
                        config['scene']['syclops_plugin_object'].append(obj_config)
                        
                        # Add transformation child for this object's frame_id
                        frame_id = obj.get('frame_id', 'iso_object')
                        if frame_id not in config['transformations']['map']['children']:
                            config['transformations']['map']['children'][frame_id] = {
                                'location': {'uniform': [[-20, -20, 0], [20, 20, 0]]},
                                'rotation': [0, 0, 0]
                            }
            except json.JSONDecodeError:
                pass  # Ignore invalid JSON
        
        # Add scatter plugins if any are configured
        scatters_data = data.get('scatters', '[]')
        if scatters_data and scatters_data != '[]':
            try:
                scatters = json.loads(scatters_data)
                if scatters:
                    config['scene']['syclops_plugin_scatter'] = []
                    for i, scatter in enumerate(scatters):
                        scatter_config = {
                            'name': scatter.get('name', f'scatter_{i}'),
                            'models': [scatter.get('model', 'Example Assets/Plain Weeds')],
                            'floor_object': scatter.get('floor_object', 'Ground'),
                            'density_max': float(scatter.get('density_max', 10)),
                            'distance_min': float(scatter.get('distance_min', 0.1)),
                            'scale_standard_deviation': float(scatter.get('scale_standard_deviation', 0.2)),
                            'seed': int(scatter.get('seed', i + 1)),
                            'class_id': int(scatter.get('class_id', i + 20)),
                            'align_to_normal': scatter.get('align_to_normal', 'true') == 'true'
                        }
                        
                        if scatter.get('max_texture_size'):
                            scatter_config['max_texture_size'] = int(scatter['max_texture_size'])
                        if scatter.get('decimate_mesh_factor'):
                            scatter_config['decimate_mesh_factor'] = float(scatter['decimate_mesh_factor'])
                        
                        config['scene']['syclops_plugin_scatter'].append(scatter_config)
            except json.JSONDecodeError:
                pass  # Ignore invalid JSON
        
        return yaml.dump(config, default_flow_style=False, indent=2)
    
    def get_available_assets(self):
        """Get available assets from the asset catalog"""
        try:
            # Try to find the asset catalog
            current_dir = Path(__file__).parent.parent
            catalog_path = current_dir / "asset_catalog.yaml"
            
            if not catalog_path.exists():
                return {'assets': [], 'error': 'Asset catalog not found'}
            
            with open(catalog_path, 'r') as f:
                catalog = yaml.safe_load(f)
            
            assets = []
            for library_name, library_data in catalog.items():
                if 'assets' in library_data:
                    for asset_name, asset_data in library_data['assets'].items():
                        if asset_data.get('type') == 'model':
                            assets.append({
                                'id': f"{library_name}/{asset_name}",
                                'name': asset_name,
                                'library': library_name,
                                'type': asset_data.get('type'),
                                'tags': asset_data.get('tags', []),
                                'thumbnail': asset_data.get('thumbnail', []),
                                'height': asset_data.get('height', 1.0)
                            })
            
            return {'assets': assets}
            
        except Exception as e:
            return {'assets': [], 'error': str(e)}
    
    def launch_asset_browser(self):
        """Launch the Syclops asset browser"""
        try:
            import subprocess
            from syclops.utility import get_or_create_install_folder, get_module_path
            
            # Get the install folder and asset browser path
            install_folder = get_or_create_install_folder()
            asset_browser_path = get_module_path("syclops.asset_manager.asset_browser")
            
            # Launch the asset browser in a new process
            subprocess.Popen([sys.executable, asset_browser_path])
            
        except Exception as e:
            raise Exception(f"Failed to launch asset browser: {str(e)}")

    def run_syclops_generation(self, config_data):
        """Run Syclops data generation with the provided configuration"""
        try:
            import subprocess
            import tempfile
            from datetime import datetime
            from syclops.utility import get_or_create_install_folder
            
            # Generate YAML config
            yaml_config = self.generate_yaml_config(config_data)
            
            # Create temporary config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.syclops.yaml', delete=False) as temp_file:
                temp_file.write(yaml_config)
                temp_config_path = temp_file.name
            
            # Get install folder
            install_folder = get_or_create_install_folder()
            
            # Get the current working directory to find syclops CLI
            current_dir = Path(__file__).parent.parent
            cli_path = current_dir / 'syclops' / 'cli.txt'
            
            # Build command to run Syclops - use direct execution of the CLI file
            python_executable = sys.executable
            cmd = [
                python_executable, 
                str(cli_path),
                '--job-description', temp_config_path,
                '--install_folder', str(install_folder)
            ]
            
            # Add debug mode if specified
            debug_mode = config_data.get('debug_mode', 'none')
            if debug_mode and debug_mode != 'none':
                cmd.extend(['--debug', debug_mode])
            
            # Start the Syclops process in background
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(current_dir)
            )
            
            # Store process info for potential monitoring
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            
            message = 'Syclops data generation started successfully!'
            note = 'Data generation is running in the background. Check the output folder for results.'
            
            if debug_mode == 'scene':
                message = 'Syclops started in debug mode! Blender UI will open to inspect the scene.'
                note = 'The Blender UI will open with the scene loaded. You can inspect and modify the scene before rendering.'
            elif debug_mode in ['blender-code', 'pipeline-code']:
                message = f'Syclops started in {debug_mode} debug mode!'
                note = 'Execution will pause for debugger attachment. Check the console for instructions.'
            
            return {
                'success': True,
                'message': message,
                'process_id': process.pid,
                'config_file': temp_config_path,
                'timestamp': timestamp,
                'command': ' '.join(cmd),
                'debug_mode': debug_mode,
                'note': note
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to start Syclops generation: {str(e)}"
            }

    def get_html(self):
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Syclops Config Generator</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            background-color: #fafafa;
        }
        .section h3 {
            margin-top: 0;
            color: #555;
            border-bottom: 2px solid #007acc;
            padding-bottom: 5px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: inline-block;
            width: 200px;
            font-weight: 500;
            color: #333;
        }
        input, select {
            width: 200px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        input[type="checkbox"] {
            width: auto;
        }
        .button-group {
            text-align: center;
            margin-top: 30px;
        }
        button {
            background-color: #007acc;
            color: white;
            border: none;
            padding: 12px 24px;
            margin: 0 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #005a9e;
        }
        .generate-data-btn {
            background-color: #28a745 !important;
            font-weight: bold;
        }
        .generate-data-btn:hover {
            background-color: #218838 !important;
        }
        .preview {
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f8f8;
            border-radius: 4px;
            border: 1px solid #ddd;
            font-family: monospace;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
            display: none;
        }
        .success-message {
            background-color: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 4px;
            margin-top: 20px;
            display: none;
        }
        .crop-item {
            border: 1px solid #ddd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            background-color: #f9f9f9;
            position: relative;
        }
        .crop-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .crop-title {
            font-weight: bold;
            color: #333;
        }
        .crop-controls {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .remove-crop {
            background-color: #dc3545;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        .remove-crop:hover {
            background-color: #c82333;
        }
        .add-button, .asset-button, .browser-button {
            background-color: #28a745;
            color: white;
            border: none;
            padding: 10px 15px;
            margin: 5px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .add-button:hover, .asset-button:hover, .browser-button:hover {
            background-color: #218838;
        }
        .asset-button {
            background-color: #17a2b8;
        }
        .asset-button:hover {
            background-color: #138496;
        }
        .browser-button {
            background-color: #6f42c1;
        }
        .browser-button:hover {
            background-color: #5a2d91;
        }
        .crop-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 10px;
        }
        .asset-modal {
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            display: none;
        }
        .asset-modal-content {
            background-color: white;
            margin: 5% auto;
            padding: 20px;
            border-radius: 8px;
            width: 80%;
            max-width: 800px;
            max-height: 70%;
            overflow-y: auto;
        }
        .asset-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .asset-card {
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 6px;
            cursor: pointer;
            text-align: center;
            transition: background-color 0.3s;
        }
        .asset-card:hover {
            background-color: #f0f0f0;
        }
        .asset-card.selected {
            background-color: #007acc;
            color: white;
        }
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .close:hover {
            color: black;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Syclops Config Generator</h1>
        
        <form id="configForm">
            <div class="section">
                <h3>Basic Settings</h3>
                <div class="form-group">
                    <label for="steps">Steps:</label>
                    <input type="number" id="steps" name="steps" value="1" min="1">
                </div>
                <div class="form-group">
                    <label for="numpy_seed">NumPy Seed:</label>
                    <input type="number" id="numpy_seed" name="numpy_seed" value="42">
                </div>
                <div class="form-group">
                    <label for="cycles_seed">Cycles Seed:</label>
                    <input type="number" id="cycles_seed" name="cycles_seed" value="42">
                </div>
                <div class="form-group">
                    <label for="debug_mode">Debug Mode:</label>
                    <select id="debug_mode" name="debug_mode">
                        <option value="none" selected>None</option>
                        <option value="scene">Scene (Open Blender UI)</option>
                        <option value="blender-code">Blender Code</option>
                        <option value="pipeline-code">Pipeline Code</option>
                    </select>
                    <small style="display: block; margin-top: 5px; color: #666;">
                        💡 <strong>Scene mode:</strong> Opens Blender UI to inspect the scene before rendering
                    </small>
                </div>
            </div>

            <div class="section">
                <h3>Render Settings</h3>
                <div class="form-group">
                    <label for="render_device">Render Device:</label>
                    <select id="render_device" name="render_device">
                        <option value="GPU" selected>GPU</option>
                        <option value="CPU">CPU</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="render_hardware">Render Hardware:</label>
                    <select id="render_hardware" name="render_hardware">
                        <option value="CUDA" selected>CUDA</option>
                        <option value="OPENCL">OpenCL</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="denoising_enabled">Enable Denoising:</label>
                    <input type="checkbox" id="denoising_enabled" name="denoising_enabled" checked>
                </div>
                <div class="form-group">
                    <label for="denoising_algorithm">Denoising Algorithm:</label>
                    <select id="denoising_algorithm" name="denoising_algorithm">
                        <option value="OPENIMAGEDENOISE" selected>OpenImageDenoise</option>
                        <option value="OPTIX">OptiX</option>
                    </select>
                </div>
            </div>

            <div class="section">
                <h3>Camera Settings</h3>
                <div class="form-group">
                    <label for="resolution_width">Resolution Width:</label>
                    <input type="number" id="resolution_width" name="resolution_width" value="2048" min="1">
                </div>
                <div class="form-group">
                    <label for="resolution_height">Resolution Height:</label>
                    <input type="number" id="resolution_height" name="resolution_height" value="2048" min="1">
                </div>
                <div class="form-group">
                    <label for="focal_length">Focal Length (mm):</label>
                    <input type="number" id="focal_length" name="focal_length" value="40" step="0.1">
                </div>
                <div class="form-group">
                    <label for="sensor_width">Sensor Width (mm):</label>
                    <input type="number" id="sensor_width" name="sensor_width" value="35" step="0.1">
                </div>
                <div class="form-group">
                    <label for="exposure">Exposure (stops):</label>
                    <input type="number" id="exposure" name="exposure" value="0.3" step="0.1">
                </div>
                <div class="form-group">
                    <label for="gamma">Gamma:</label>
                    <input type="number" id="gamma" name="gamma" value="1.4" step="0.1">
                </div>
            </div>

            <div class="section">
                <h3>Scene Settings</h3>
                <div class="form-group">
                    <label for="ground_size">Ground Size (m):</label>
                    <input type="number" id="ground_size" name="ground_size" value="50" min="1">
                </div>
                <div class="form-group">
                    <label for="ground_texture">Ground Texture:</label>
                    <input type="text" id="ground_texture" name="ground_texture" value="Example Assets/Muddy Dry Ground">
                </div>
                <div class="form-group">
                    <label for="environment">Environment HDRI:</label>
                    <input type="text" id="environment" name="environment" value="Assets_own/Field">
                </div>
            </div>

            <div class="section">
                <h3>Crop Configuration</h3>
                <div class="form-group">
                    <button type="button" onclick="addCrop()" class="add-button">➕ Add Crop</button>
                    <button type="button" onclick="loadAssets()" class="asset-button">📋 Load Available Assets</button>
                    <button type="button" onclick="launchAssetBrowser()" class="browser-button">🔍 Open Asset Browser</button>
                </div>
                <div id="crops-container">
                    <!-- Crops will be added dynamically here -->
                </div>
                <input type="hidden" id="crops" name="crops" value="[]">
            </div>

            <div class="section">
                <h3>Object Plugin Configuration</h3>
                <div class="form-group">
                    <button type="button" onclick="addObject()" class="add-button">➕ Add Object</button>
                </div>
                <div id="objects-container">
                    <!-- Objects will be added dynamically here -->
                </div>
                <input type="hidden" id="objects" name="objects" value="[]">
            </div>

            <div class="section">
                <h3>Scatter Plugin Configuration</h3>
                <div class="form-group">
                    <button type="button" onclick="addScatter()" class="add-button">➕ Add Scatter</button>
                </div>
                <div id="scatter-container">
                    <!-- Scatter configs will be added dynamically here -->
                </div>
                <input type="hidden" id="scatters" name="scatters" value="[]">
            </div>

            <div class="button-group">
                <button type="button" onclick="previewConfig()">Preview Config</button>
                <button type="button" onclick="generateConfig()">Generate & Download Config</button>
                <button type="button" onclick="generateData()" class="generate-data-btn">🚀 Generate Data</button>
            </div>
        </form>

        <div id="preview" class="preview"></div>
        <div id="successMessage" class="success-message"></div>
    </div>

    <!-- Asset Selection Modal -->
    <div id="assetModal" class="asset-modal">
        <div class="asset-modal-content">
            <span class="close" onclick="closeAssetModal()">&times;</span>
            <h3>Select Asset</h3>
            <div id="assetGrid" class="asset-grid">
                <!-- Assets will be loaded here -->
            </div>
            <div style="text-align: center; margin-top: 20px;">
                <button type="button" onclick="selectAsset()">Select Asset</button>
                <button type="button" onclick="closeAssetModal()">Cancel</button>
            </div>
        </div>
    </div>

    <script src="config.js"></script>
</body>
</html>"""

    def get_js(self):
        return """
function getFormData() {
    const form = document.getElementById('configForm');
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    // Handle checkbox
    data.denoising_enabled = document.getElementById('denoising_enabled').checked;
    
    
    // Handle crops data
    data.crops = document.getElementById('crops').value;
    
    // Handle objects data
    data.objects = document.getElementById('objects').value;
    
    // Handle scatters data
    data.scatters = document.getElementById('scatters').value;
    
    return data;
}

let cropCounter = 0;
let availableAssets = [];
let currentCropForAssetSelection = null;
let currentAssetSelectionType = 'crop'; // 'crop', 'object', or 'scatter'

function addCrop() {
    cropCounter++;
    const cropsContainer = document.getElementById('crops-container');
    
    const cropDiv = document.createElement('div');
    cropDiv.className = 'crop-item';
    cropDiv.id = `crop-${cropCounter}`;
    
    cropDiv.innerHTML = `
        <div class="crop-header">
            <span class="crop-title">Crop ${cropCounter}</span>
            <div class="crop-controls">
                <button type="button" onclick="selectAssetForCrop(${cropCounter})" class="asset-button">Select Asset</button>
                <button type="button" onclick="removeCrop(${cropCounter})" class="remove-crop">Remove</button>
            </div>
        </div>
        <div class="crop-row">
            <div class="form-group">
                <label>Name:</label>
                <input type="text" id="crop_${cropCounter}_name" value="crop_${cropCounter}">
            </div>
            <div class="form-group">
                <label>Model:</label>
                <input type="text" id="crop_${cropCounter}_model" value="Assets_own/bbch_15" readonly>
            </div>
        </div>
        <div class="crop-row">
            <div class="form-group">
                <label>Crop Angle (degrees):</label>
                <input type="number" id="crop_${cropCounter}_crop_angle" value="0" min="-90" max="90">
            </div>
            <div class="form-group">
                <label>Class ID:</label>
                <input type="number" id="crop_${cropCounter}_class_id" value="${cropCounter + 1}" min="1">
            </div>
        </div>
        <div class="crop-row">
            <div class="form-group">
                <label>Row Distance (m):</label>
                <input type="number" id="crop_${cropCounter}_row_distance" value="0.8" step="0.1" min="0">
            </div>
            <div class="form-group">
                <label>Row Std Dev (m):</label>
                <input type="number" id="crop_${cropCounter}_row_standard_deviation" value="0.32" step="0.01" min="0">
            </div>
        </div>
        <div class="crop-row">
            <div class="form-group">
                <label>Plant Distance (m):</label>
                <input type="number" id="crop_${cropCounter}_plant_distance" value="0.4" step="0.1" min="0">
            </div>
            <div class="form-group">
                <label>Plant Std Dev (m):</label>
                <input type="number" id="crop_${cropCounter}_plant_standard_deviation" value="0.2" step="0.01" min="0">
            </div>
        </div>
        <div class="crop-row">
            <div class="form-group">
                <label>Scale Std Dev:</label>
                <input type="number" id="crop_${cropCounter}_scale_standard_deviation" value="0.5" step="0.1" min="0">
            </div>
            <div class="form-group">
                <label>Seed:</label>
                <input type="number" id="crop_${cropCounter}_seed" value="${cropCounter}" min="1">
            </div>
        </div>
    `;
    
    cropsContainer.appendChild(cropDiv);
    updateCropsData();
}

function removeCrop(cropId) {
    const cropElement = document.getElementById(`crop-${cropId}`);
    if (cropElement) {
        cropElement.remove();
        updateCropsData();
    }
}

function updateCropsData() {
    const crops = [];
    const cropsContainer = document.getElementById('crops-container');
    const cropItems = cropsContainer.querySelectorAll('.crop-item');
    
    cropItems.forEach(item => {
        const id = item.id.replace('crop-', '');
        const crop = {
            name: document.getElementById(`crop_${id}_name`).value,
            model: document.getElementById(`crop_${id}_model`).value,
            crop_angle: document.getElementById(`crop_${id}_crop_angle`).value,
            class_id: document.getElementById(`crop_${id}_class_id`).value,
            row_distance: document.getElementById(`crop_${id}_row_distance`).value,
            row_standard_deviation: document.getElementById(`crop_${id}_row_standard_deviation`).value,
            plant_distance: document.getElementById(`crop_${id}_plant_distance`).value,
            plant_standard_deviation: document.getElementById(`crop_${id}_plant_standard_deviation`).value,
            scale_standard_deviation: document.getElementById(`crop_${id}_scale_standard_deviation`).value,
            seed: document.getElementById(`crop_${id}_seed`).value
        };
        crops.push(crop);
    });
    
    document.getElementById('crops').value = JSON.stringify(crops);
}

// Object Plugin Functions
let objectCounter = 0;

function addObject() {
    objectCounter++;
    const objectsContainer = document.getElementById('objects-container');
    
    const objectDiv = document.createElement('div');
    objectDiv.className = 'crop-item';
    objectDiv.id = `object-${objectCounter}`;
    
    objectDiv.innerHTML = `
        <div class="crop-header">
            <span class="crop-title">Object ${objectCounter}</span>
            <button type="button" onclick="removeObject(${objectCounter})" class="remove-crop">Remove</button>
        </div>
        <div class="crop-row">
            <div class="form-group">
                <label>Name:</label>
                <input type="text" id="object_${objectCounter}_name" value="object_${objectCounter}">
            </div>
            <div class="form-group">
                <label>Model:</label>
                <input type="text" id="object_${objectCounter}_model" value="Example Assets/ISO Object">
                <button type="button" onclick="openAssetModalForObject(${objectCounter})" style="padding: 5px 10px; font-size: 12px;">Select</button>
            </div>
        </div>
        <div class="crop-row">
            <div class="form-group">
                <label>Frame ID:</label>
                <input type="text" id="object_${objectCounter}_frame_id" value="iso_object">
            </div>
            <div class="form-group">
                <label>Class ID:</label>
                <input type="number" id="object_${objectCounter}_class_id" value="${objectCounter + 10}" min="1">
            </div>
        </div>
        <div class="crop-row">
            <div class="form-group">
                <label>Place on Ground:</label>
                <input type="checkbox" id="object_${objectCounter}_place_on_ground">
            </div>
            <div class="form-group">
                <label>Floor Object:</label>
                <input type="text" id="object_${objectCounter}_floor_object" value="Ground">
            </div>
        </div>
        <div class="crop-row">
            <div class="form-group">
                <label>Max Texture Size:</label>
                <input type="number" id="object_${objectCounter}_max_texture_size" value="2048" min="256" step="256">
            </div>
            <div class="form-group">
                <label>Decimate Factor:</label>
                <input type="number" id="object_${objectCounter}_decimate_mesh_factor" value="1.0" min="0" max="1" step="0.1">
            </div>
        </div>
    `;
    
    objectsContainer.appendChild(objectDiv);
    updateObjectsData();
}

function removeObject(objectId) {
    const objectElement = document.getElementById(`object-${objectId}`);
    if (objectElement) {
        objectElement.remove();
        updateObjectsData();
    }
}

function updateObjectsData() {
    const objects = [];
    const objectsContainer = document.getElementById('objects-container');
    const objectItems = objectsContainer.querySelectorAll('.crop-item');
    
    objectItems.forEach(item => {
        const id = item.id.replace('object-', '');
        const obj = {
            name: document.getElementById(`object_${id}_name`).value,
            model: document.getElementById(`object_${id}_model`).value,
            frame_id: document.getElementById(`object_${id}_frame_id`).value,
            class_id: document.getElementById(`object_${id}_class_id`).value,
            place_on_ground: document.getElementById(`object_${id}_place_on_ground`).checked ? 'true' : 'false',
            floor_object: document.getElementById(`object_${id}_floor_object`).value,
            max_texture_size: document.getElementById(`object_${id}_max_texture_size`).value,
            decimate_mesh_factor: document.getElementById(`object_${id}_decimate_mesh_factor`).value
        };
        objects.push(obj);
    });
    
    document.getElementById('objects').value = JSON.stringify(objects);
}

function openAssetModalForObject(objectId) {
    if (availableAssets.length === 0) {
        alert('Please load assets first by clicking "Load Available Assets"');
        return;
    }
    currentCropForAssetSelection = objectId;
    currentAssetSelectionType = 'object';
    displayAssetModal();
}

// Scatter Plugin Functions
let scatterCounter = 0;

function addScatter() {
    scatterCounter++;
    const scatterContainer = document.getElementById('scatter-container');
    
    const scatterDiv = document.createElement('div');
    scatterDiv.className = 'crop-item';
    scatterDiv.id = `scatter-${scatterCounter}`;
    
    scatterDiv.innerHTML = `
        <div class="crop-header">
            <span class="crop-title">Scatter ${scatterCounter}</span>
            <button type="button" onclick="removeScatter(${scatterCounter})" class="remove-crop">Remove</button>
        </div>
        <div class="crop-row">
            <div class="form-group">
                <label>Name:</label>
                <input type="text" id="scatter_${scatterCounter}_name" value="scatter_${scatterCounter}">
            </div>
            <div class="form-group">
                <label>Model:</label>
                <input type="text" id="scatter_${scatterCounter}_model" value="Example Assets/Plain Weeds">
                <button type="button" onclick="openAssetModalForScatter(${scatterCounter})" style="padding: 5px 10px; font-size: 12px;">Select</button>
            </div>
        </div>
        <div class="crop-row">
            <div class="form-group">
                <label>Floor Object:</label>
                <input type="text" id="scatter_${scatterCounter}_floor_object" value="Ground">
            </div>
            <div class="form-group">
                <label>Class ID:</label>
                <input type="number" id="scatter_${scatterCounter}_class_id" value="${scatterCounter + 20}" min="1">
            </div>
        </div>
        <div class="crop-row">
            <div class="form-group">
                <label>Density Max (per m²):</label>
                <input type="number" id="scatter_${scatterCounter}_density_max" value="10" min="0" step="0.1">
            </div>
            <div class="form-group">
                <label>Distance Min (m):</label>
                <input type="number" id="scatter_${scatterCounter}_distance_min" value="0.1" min="0" step="0.01">
            </div>
        </div>
        <div class="crop-row">
            <div class="form-group">
                <label>Scale Std Dev:</label>
                <input type="number" id="scatter_${scatterCounter}_scale_standard_deviation" value="0.2" min="0" step="0.1">
            </div>
            <div class="form-group">
                <label>Seed:</label>
                <input type="number" id="scatter_${scatterCounter}_seed" value="${scatterCounter}" min="1">
            </div>
        </div>
        <div class="crop-row">
            <div class="form-group">
                <label>Align to Normal:</label>
                <input type="checkbox" id="scatter_${scatterCounter}_align_to_normal" checked>
            </div>
            <div class="form-group">
                <label>Decimate Factor:</label>
                <input type="number" id="scatter_${scatterCounter}_decimate_mesh_factor" value="1.0" min="0" max="1" step="0.1">
            </div>
        </div>
    `;
    
    scatterContainer.appendChild(scatterDiv);
    updateScattersData();
}

function removeScatter(scatterId) {
    const scatterElement = document.getElementById(`scatter-${scatterId}`);
    if (scatterElement) {
        scatterElement.remove();
        updateScattersData();
    }
}

function updateScattersData() {
    const scatters = [];
    const scatterContainer = document.getElementById('scatter-container');
    const scatterItems = scatterContainer.querySelectorAll('.crop-item');
    
    scatterItems.forEach(item => {
        const id = item.id.replace('scatter-', '');
        const scatter = {
            name: document.getElementById(`scatter_${id}_name`).value,
            model: document.getElementById(`scatter_${id}_model`).value,
            floor_object: document.getElementById(`scatter_${id}_floor_object`).value,
            class_id: document.getElementById(`scatter_${id}_class_id`).value,
            density_max: document.getElementById(`scatter_${id}_density_max`).value,
            distance_min: document.getElementById(`scatter_${id}_distance_min`).value,
            scale_standard_deviation: document.getElementById(`scatter_${id}_scale_standard_deviation`).value,
            seed: document.getElementById(`scatter_${id}_seed`).value,
            align_to_normal: document.getElementById(`scatter_${id}_align_to_normal`).checked ? 'true' : 'false',
            decimate_mesh_factor: document.getElementById(`scatter_${id}_decimate_mesh_factor`).value
        };
        scatters.push(scatter);
    });
    
    document.getElementById('scatters').value = JSON.stringify(scatters);
}

function openAssetModalForScatter(scatterId) {
    if (availableAssets.length === 0) {
        alert('Please load assets first by clicking "Load Available Assets"');
        return;
    }
    currentCropForAssetSelection = scatterId;
    currentAssetSelectionType = 'scatter';
    displayAssetModal();
}

function loadAssets() {
    fetch('/get_assets', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.assets) {
            availableAssets = result.assets;
            alert(`Loaded ${result.assets.length} available assets.`);
        } else {
            alert('Error loading assets: ' + (result.error || 'Unknown error'));
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
}

function selectAssetForCrop(cropId) {
    if (availableAssets.length === 0) {
        alert('Please load assets first by clicking "Load Available Assets"');
        return;
    }
    
    currentCropForAssetSelection = cropId;
    currentAssetSelectionType = 'crop';
    displayAssetModal();
}

function displayAssetModal() {
    const modal = document.getElementById('assetModal');
    const assetGrid = document.getElementById('assetGrid');
    
    assetGrid.innerHTML = '';
    
    availableAssets.forEach(asset => {
        const assetCard = document.createElement('div');
        assetCard.className = 'asset-card';
        assetCard.onclick = () => selectAssetCard(assetCard, asset);
        
        assetCard.innerHTML = `
            <h4>${asset.name}</h4>
            <p><small>${asset.library}</small></p>
            <p><small>Type: ${asset.type}</small></p>
            ${asset.tags.length > 0 ? `<p><small>Tags: ${asset.tags.join(', ')}</small></p>` : ''}
        `;
        
        assetGrid.appendChild(assetCard);
    });
    
    modal.style.display = 'block';
}

function selectAssetCard(cardElement, asset) {
    // Remove selection from other cards
    const cards = document.querySelectorAll('.asset-card');
    cards.forEach(card => card.classList.remove('selected'));
    
    // Select this card
    cardElement.classList.add('selected');
    cardElement.selectedAsset = asset;
}

function selectAsset() {
    const selectedCard = document.querySelector('.asset-card.selected');
    if (!selectedCard || !selectedCard.selectedAsset) {
        alert('Please select an asset first');
        return;
    }
    
    const asset = selectedCard.selectedAsset;
    let modelInput = null;
    
    // Determine which input field to update based on selection type
    if (currentAssetSelectionType === 'crop') {
        modelInput = document.getElementById(`crop_${currentCropForAssetSelection}_model`);
        if (modelInput) {
            modelInput.value = asset.id;
            updateCropsData();
        }
    } else if (currentAssetSelectionType === 'object') {
        modelInput = document.getElementById(`object_${currentCropForAssetSelection}_model`);
        if (modelInput) {
            modelInput.value = asset.id;
            updateObjectsData();
        }
    } else if (currentAssetSelectionType === 'scatter') {
        modelInput = document.getElementById(`scatter_${currentCropForAssetSelection}_model`);
        if (modelInput) {
            modelInput.value = asset.id;
            updateScattersData();
        }
    }
    
    closeAssetModal();
}

function closeAssetModal() {
    document.getElementById('assetModal').style.display = 'none';
    currentCropForAssetSelection = null;
}

function launchAssetBrowser() {
    fetch('/launch_asset_browser', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('Asset browser launched! You can use it to browse and manage your assets.');
        } else {
            alert('Error launching asset browser: ' + result.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
}

// Add event listeners to update data when inputs change
document.addEventListener('change', function(e) {
    if (e.target.id.startsWith('crop_')) {
        updateCropsData();
    } else if (e.target.id.startsWith('object_')) {
        updateObjectsData();
    } else if (e.target.id.startsWith('scatter_')) {
        updateScattersData();
    }
});

function previewConfig() {
    const data = getFormData();
    
    fetch('/save_config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            const preview = document.getElementById('preview');
            preview.textContent = result.yaml_content;
            preview.style.display = 'block';
        } else {
            alert('Error generating config: ' + result.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
}

function generateConfig() {
    const data = getFormData();
    
    fetch('/save_config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // Create download link
            const blob = new Blob([result.yaml_content], { type: 'text/yaml' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'syclops_config.yaml';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            const successMsg = document.getElementById('successMessage');
            successMsg.textContent = 'Config file generated and downloaded successfully!';
            successMsg.style.display = 'block';
            
            setTimeout(() => {
                successMsg.style.display = 'none';
            }, 3000);
        } else {
            alert('Error generating config: ' + result.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
}

function generateData() {
    const data = getFormData();
    
    // Show confirmation dialog
    const confirmed = confirm(
        'This will start Syclops data generation with your current configuration.\\n\\n' +
        'The process may take several minutes to complete depending on your settings.\\n\\n' +
        'Do you want to continue?'
    );
    
    if (!confirmed) {
        return;
    }
    
    // Disable the button to prevent multiple clicks
    const generateBtn = document.querySelector('.generate-data-btn');
    const originalText = generateBtn.textContent;
    generateBtn.disabled = true;
    generateBtn.textContent = '⏳ Generating...';
    
    fetch('/generate_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        // Re-enable the button
        generateBtn.disabled = false;
        generateBtn.textContent = originalText;
        
        if (result.success) {
            const successMsg = document.getElementById('successMessage');
            
            let debugInfo = '';
            if (result.debug_mode && result.debug_mode !== 'none') {
                debugInfo = `<p><strong>🐛 Debug Mode:</strong> ${result.debug_mode}</p>`;
            }
            
            successMsg.innerHTML = `
                <h4>🎉 ${result.message}</h4>
                <p><strong>Process ID:</strong> ${result.process_id}</p>
                <p><strong>Timestamp:</strong> ${result.timestamp}</p>
                ${debugInfo}
                <p><strong>Config File:</strong> ${result.config_file}</p>
                <p><strong>Command:</strong> <code style="font-size: 11px;">${result.command}</code></p>
                <p><em>${result.note}</em></p>
            `;
            successMsg.style.display = 'block';
            
            // Auto-hide after 10 seconds (or 15 for debug mode)
            const hideDelay = (result.debug_mode && result.debug_mode !== 'none') ? 15000 : 10000;
            setTimeout(() => {
                successMsg.style.display = 'none';
            }, hideDelay);
            
            // Also show alert for immediate feedback
            let alertMsg = result.message;
            if (result.debug_mode === 'scene') {
                alertMsg += '\\n\\nBlender UI will open shortly for scene inspection.';
            }
            alert(alertMsg);
        } else {
            alert('Error starting data generation: ' + result.error);
        }
    })
    .catch(error => {
        // Re-enable the button
        generateBtn.disabled = false;
        generateBtn.textContent = originalText;
        alert('Error: ' + error);
    });
}"""


def start_server(port=8080):
    """Start the web server"""
    try:
        with socketserver.TCPServer(("", port), ConfigHandler) as httpd:
            print(f"🚀 Syclops Config UI started at http://localhost:{port}")
            print("📝 Open the URL in your browser to create config files")
            print("⏹️  Press Ctrl+C to stop the server")
            
            # Try to open browser automatically
            def open_browser():
                time.sleep(1)
                webbrowser.open(f'http://localhost:{port}')
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Trying port {port + 1}...")
            start_server(port + 1)
        else:
            print(f"❌ Error starting server: {e}")


def main():
    print("🎬 Syclops Configuration UI")
    print("=" * 50)
    start_server()


if __name__ == "__main__":
    main()
