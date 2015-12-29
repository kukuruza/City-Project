require 'sketchup.rb'

def setOriginToCenter 
    bb = Geom::BoundingBox.new ;   # Outter Shell 
    Sketchup.active_model.entities.each {|e| bb.add(e.bounds) ; } 

    vector = Geom::Vector3d.new -bb.center[0], -bb.center[1], 0
    transformation = Geom::Transformation.translation vector

    entities = Sketchup.active_model.entities
    entities.transform_entities(transformation, entities.to_a)
end

def orientAlongX
    bb = Sketchup.active_model.bounds 
    center = bb.center

    if bb.width < bb.height
        print ('bb.width < bb.height: will rotate')
        vectorUp = Geom::Vector3d.new 0,0,1
        origin   = Geom::Point3d.new 0,0,0
        rot = Geom::Transformation.rotation origin, vectorUp, Math::PI / 2

        entities = Sketchup.active_model.entities
        entities.transform_entities(rot, entities.to_a)
    else
        print ('bb.width >= bb.height: leave as it is')
    end
end

def rotate180
    vectorUp = Geom::Vector3d.new 0,0,1
    origin   = Geom::Point3d.new 0,0,0
    rot = Geom::Transformation.rotation origin, vectorUp, Math::PI

    entities = Sketchup.active_model.entities
    entities.transform_entities(rot, entities.to_a)
end

def exportObj (filepath)
    Sketchup.active_model.export filepath
end

#=============================================================================

if( not file_loaded?("centerpoint.rb") )
    UI.menu("Plugins").add_item("Set Origin To Center") { setOriginToCenter }
    UI.menu("Plugins").add_item("Orient Along X") { orientAlongX }
    UI.menu("Plugins").add_item("Rotate 180") { rotate180 }
end
#-----------------------------------------------------------------------------
file_loaded("centerpoint.rb")

