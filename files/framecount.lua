INITIAL_FRAME=-1

function g_framecount()
    if(INITIAL_FRAME == -1)
    then
        INITIAL_FRAME = fba.framecount()
    end
    TOTAL_FRAMES = fba.framecount() - INITIAL_FRAME
    -- Write out the frame count ever 0.1 seconds ( roughly )
    if TOTAL_FRAMES % 10 == 0 then
        print(TOTAL_FRAMES)
        file = io.open("framecount.txt", "w")
        file:write(TOTAL_FRAMES)
        file:close()
    end
end

-- Frame count doesn't reset after f3
emu.registerafter(function() g_framecount() end)
